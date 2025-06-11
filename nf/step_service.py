from utils.logger import setup_logger
from utils.logger2 import logger
from nf import prepaid_ctl_service as pctl
from nf import flow_service as flow
from nf import keyword_service as key
from nf import extension_expiry_service as ees
from nf.nf_constants import NfConstants

# logger = setup_logger(service_name=f"NF {__name__}")

# Call Constants
nf = NfConstants()


# Function to start Steps service loop using BS successfully created rows/row
def nf_start_service_steps(bs_worksheet, bs_success_rows, webdriver, gsheet):
    logger.info("STARTING STEP SERVICE")
    global wd
    global gs

    wd = webdriver
    gs = gsheet

    # Start looping all the bulk service success rows for 'Steps and Flow Construct' process
    for row in bs_success_rows:
        try:
            # Declare Variables and Get Current row values
            bs_row_data = bs_worksheet.row_values(row)
            bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
            with_double_flow_value = bs_row_data[nf.NF_INDEX_WITH_DOUBLE_FLOW].lower()
            with_extend_steps_and_flow_value = bs_row_data[
                nf.NF_INDEX_WITH_EXTEND_STEPS_AND_FLOW
            ].lower()

            # Declare Dictionary of Double and Extend condition to handle if there's double and/or extend flow.
            double_extend_conditions = {
                # Always 'True' include for Standard Flow
                "": True,
                # Controlled by Double Flow from gsheet
                "double": (True if with_double_flow_value == "yes" else False),
                # Controlled by Double Flow from gsheet
                "extend": (
                    True if with_extend_steps_and_flow_value == "yes" else False
                ),
            }

            # Create worksheet for ParamMatrix
            param_worksheet = gs.create_worksheet(
                nf.WORKSHEET_TAB_BULK_SERVICES_TAB_PARAM_MATRIX
            )

            # Declare old_step_type_data and old_extend_step_id before loop, to update and maintain old data and to reuse for double and extend flow
            old_step_type_data = {}
            old_extend_step_id = None

            # Section to start loop for standard, double and/or extend Step Type and Flow.
            for (
                double_extend_value,
                double_extend_true,
            ) in double_extend_conditions.items():
                logger.info(
                    f"CURRENT LOOP: {'STANDARD' if double_extend_value == '' else double_extend_value.upper()}"
                )
                if double_extend_true:
                    logger.info(f"Bulk Service Data Row {row}: {bs_row_data}")

                    # Start Steps and Flow construct proccess and return dictionary step details = STEP ID and STEP NAME in dictionary format
                    step_type_data, old_incharge_extend_data = create_step(
                        double_extend_value,
                        old_extend_step_id,
                        bs_row_data,
                        param_worksheet,
                        row,
                    )
                    # Section to Store the IN CHARGE and EXTEND FIRST EXPIRY data to a temporary variable dictionary to use it for double flow process TEMPORARY DICTIONARY = old_step_type_data
                    # Condition for Standard Flow to start storing the data
                    if (
                        double_extend_value != "double"
                        and double_extend_value != "extend"
                    ):
                        logger.info(
                            f"STORING DATA TO TEMP. VARIABLE: {old_incharge_extend_data}"
                        )
                        # To use for Double Flow - old_step_type_data
                        old_step_type_data.update(old_incharge_extend_data)

                        # To use for Extend Flow - old_extend_step_id
                        old_extend_step_id = old_incharge_extend_data[
                            "extend_first_expiry_id"
                        ]
                    # Condition for Double Flow to start using the previous IN CHARGE and EXTEND FIRST EXPIRY data by updating it to step_type_data
                    elif double_extend_value == "double":
                        logger.info(
                            f"RE-USING IN CHARGE AND EXTEND FIRST EXPIRY DATA: {old_step_type_data}"
                        )
                        step_type_data.update(old_step_type_data)

                    # Condition for Extend Flow to start using the previous EXTEND FIRST EXPIRY WITH ADDITIONAL PARAM data by updating it to step_type_data
                    elif double_extend_value == "extend":
                        logger.info(f"RE-USING EXTEND HLR - PLY {old_step_type_data}")
                        # old_step_type_data.clear()
                        step_type_data["hlr_ply_id"] = old_step_type_data["hlr_ply_id"]
                        step_type_data["hlr_ply_name"] = old_step_type_data[
                            "hlr_ply_name"
                        ]

                    # Start Flow Process to Define Flow from 'step_from' to 'step_to'
                    flow.nf_start_service_flows(
                        double_extend_value,
                        step_type_data,
                        bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT],
                        bs_row_data[nf.NF_INDEX_SERVICE_ID],
                        bs_worksheet,
                        wd,
                        gs,
                        row,
                    )

                    if double_extend_true == "extend":
                        # Start Keyword Process (For Extend Flow only)
                        key.create_keyword(
                            bs_service_id, bs_row_data, wd, gs, double_extend_value
                        )

                        # Start Extension Expiry Service
                        ees.create_extension_expiry(bs_service_id, bs_row_data, wd)

        except Exception as e:
            error_msg = f"An error has occurred on 'start_nf_service_steps' function\n ERROR: {e}"
            logger.info(error_msg)
            gs.update_rpa_remarks_error(row, error_msg, bs_worksheet)
            continue


# Funcion to handle/to determine what step and flow construct to execute
def create_step(
    double_extend_value, old_extend_step_id, bs_row_data, param_worksheet, row
):
    # --------------------START STEP PROCESS------------------------#
    try:
        # Declare bs_service_id value from bulk service service id and step_and_flow_construct_value
        bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
        step_and_flow_construct_value = bs_row_data[
            nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT
        ].lower()

        logger.info(
            f"STARTING DEFINING STEPS FOR: {bs_service_id} = {bs_row_data[nf.NF_INDEX_NAME]}"
        )

        # Determine what specific process to defining steps and flows for bulk services.
        # Execute Process For Step Type = Prepaid CTL With Data
        logger.info(
            f"Step and Flow Construct - Executing Process => '{bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]}' - With Double Flow?: {bs_row_data[nf.NF_INDEX_WITH_DOUBLE_FLOW]} - With Extend Steps and Flow?: {bs_row_data[nf.NF_INDEX_WITH_EXTEND_STEPS_AND_FLOW]}"
        )

        # Calling function to execute step type services for Prepaid CTL
        if "prepaid ctl" in step_and_flow_construct_value:
            step_type_data, incharge_extend_data = pctl.start_construct_prepaid_ctl(
                double_extend_value,
                old_extend_step_id,
                bs_service_id,
                bs_row_data,
                param_worksheet,
                wd,
                gs,
            )

            return step_type_data, incharge_extend_data

        # Calling function to execute step type services for Prepaid OPM
        elif "prepaid opm" in bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT].lower():
            "TODO"

        else:
            logger.info(
                f"Value doesn't recognize '{bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]}' to process for steps and flows construct."
            )

    except Exception as e:
        error_msg = f"Something went wrong in the Process Sequence of 'SERVICE STEP TYPE PROCESS'.\nERROR: {e}"
        logger.info(error_msg)
        logger.info("Terminating Bot")
        wd.stop_process()
