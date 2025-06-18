from utils.logger import setup_logger
from utils.env_loader import get_env_variable
from utils.logger2 import logger
from nf.prepaid_services import prepaid_ctl_service as pctl
from nf.main_services import flow_service as flow
from nf.main_services import keyword_service as key
from nf.main_services import extension_expiry_service as ees
from nf.main_services import ssg_service as ssg
from nf.nf_constants import NfConstants

# logger = setup_logger(service_name=f"NF {__name__}")

# Call Constants
nf = NfConstants()


# Function to start Steps service loop using BS successfully created rows/row
def start_step_and_flow_construct(bs_worksheet, bs_success_rows, webdriver, gsheet):
    logger.info("STARTING STEP SERVICE")
    global wd
    global gs

    wd = webdriver
    gs = gsheet

    # Section to start loop for all bulk services that are successfully created using array rows for loop
    for row in bs_success_rows:
        try:
            # Get Current Bulk Service row values
            bs_data = bs_worksheet.row_values(row)

            # Declare Variables
            bs_service_id = bs_data[nf.NF_INDEX_SERVICE_ID]
            with_double_flow_value = bs_data[nf.NF_INDEX_WITH_DOUBLE_FLOW].lower()
            with_extend_steps_and_flow_value = bs_data[
                nf.NF_INDEX_WITH_EXTEND_STEPS_AND_FLOW
            ].lower()

            # Declare Dictionary of Base, Double and Extend condition to handle if there's a double and/or extend flow.
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

            # Section to start nested loop for standard, double and/or extend Step Type and Flow.
            for (
                double_extend_key,
                double_extend_true,
            ) in double_extend_conditions.items():
                logger.info(
                    f"CURRENT LOOP: {'BASE' if double_extend_key == '' else double_extend_key.upper()} FLOW"
                )
                if double_extend_true:
                    bs_row_data = bs_worksheet.row_values(row)
                    logger.info(f"Bulk Service Data Row {row}: {bs_row_data}")

                    # Start Steps and Flow construct proccess and return dictionary step details = STEP ID and STEP NAME in dictionary format
                    step_type_data, old_incharge_extend_data = create_step(
                        double_extend_key,
                        old_extend_step_id,
                        bs_row_data,
                        param_worksheet,
                        row,
                    )

                    ############ SECTION FOR STEP TYPE DATA MANIPULATION ##############
                    ############ LOOP WHEN IN BASE FLOW ##############
                    # Section to Store the IN CHARGE and EXTEND FIRST EXPIRY data to a temporary variable dictionary to use it for double flow process TEMPORARY DICTIONARY = old_step_type_data
                    # Condition for Base Flow to start storing the data
                    if double_extend_key != "double" and double_extend_key != "extend":
                        logger.info(
                            f"STORING DATA TO TEMP. VARIABLE: {old_incharge_extend_data}"
                        )
                        # To use for Double Flow - old_step_type_data
                        old_step_type_data.update(old_incharge_extend_data)

                        # To use for Extend Flow - old_extend_step_id
                        old_extend_step_id = old_incharge_extend_data[
                            "extend_first_expiry_id"
                        ]
                    ######################################

                    ############ LOOP WHEN IN DOUBLE FLOW ##############
                    # Condition for Double Flow to start using the previous IN CHARGE and EXTEND FIRST EXPIRY data by updating it to step_type_data
                    elif double_extend_key == "double":
                        logger.info(
                            f"RE-USING IN CHARGE AND EXTEND FIRST EXPIRY DATA: {old_step_type_data}"
                        )
                        step_type_data.update(old_step_type_data)
                    #######################################

                    ############ LOOP WHEN IN EXTEND FLOW ##############
                    # Condition for Extend Flow to start using the previous EXTEND FIRST EXPIRY WITH ADDITIONAL PARAM data by updating it to step_type_data

                    elif (
                        double_extend_key == "extend"
                        and "hlr_ply_id" in old_step_type_data
                    ):
                        logger.info(f"RE-USING EXTEND HLR - PLY {old_step_type_data}")
                        # old_step_type_data.clear()
                        step_type_data["hlr_ply_id"] = old_step_type_data["hlr_ply_id"]
                        step_type_data["hlr_ply_name"] = old_step_type_data[
                            "hlr_ply_name"
                        ]
                    #######################################

                    # Start Flow Process to Define Flow from 'step_from' to 'step_to'
                    flow.nf_start_service_flows(
                        double_extend_key,
                        step_type_data,
                        bs_worksheet,
                        wd,
                        gs,
                        row,
                    )

                    #### EXTEND FLOW - CREATE KEYWORD AND EXTENSION EXPIRY ####
                    if double_extend_key == "extend":
                        # Start Keyword Process (For Extend Flow only)
                        key.create_keyword(
                            bs_service_id, bs_row_data, wd, double_extend_key
                        )
                        # Start Extension Expiry Service
                        ees.create_extension_expiry(bs_service_id, bs_row_data, wd)

            # Start Defining Gyro Command
            if not bs_row_data[nf.BS_INDEX_GYRO_COMMAND]:
                pass
            else:
                create_gyro_command(
                    bs_row_data[nf.BS_INDEX_GYRO_COMMAND], bs_service_id, wd
                )

                # Update RPA Remarks when Gyro Success
                bs_row_data_updated_1 = bs_worksheet.row_values(row)
                rpa_remarks_gyro = (
                    f"{bs_row_data_updated_1[nf.NF_INDEX_RPA_REMARKS]} | GYRO: SUCCESS"
                )
                gs.update_row(
                    row,
                    nf.COLUMN_BULK_SERVICE_RPA_REMARKS,
                    bs_worksheet,
                    rpa_remarks_gyro,
                )

            # Start Defining Current Bulk Service in Simple Service Group DATA BAL
            if bs_row_data[nf.NF_INDEX_GROUP_STATUS_INQUIRY].lower() == "yes":
                bs_row_data_updated_2 = bs_worksheet.row_values(row)
                ssg.define_bs_simple_service_group(bs_service_id, wd)

                # Update RPA Remarks when Simple Service Group Success
                rpa_remarks_ssg = f"{bs_row_data_updated_2[nf.NF_INDEX_RPA_REMARKS]} | SIMPLE SERVICE GROUP: SUCCESS"
                gs.update_row(
                    row,
                    nf.COLUMN_BULK_SERVICE_RPA_REMARKS,
                    bs_worksheet,
                    rpa_remarks_ssg,
                )
            try:
                # Update Gsheet by inserting bulk service id to gsheet tab 'Message' service id column
                logger.info("Inserting Bulk Service Id to 'Messages' worksheet..")
                # Create Worksheet For Messages
                logger.info("Creating Worksheet for 'Messages'...")
                messages_worksheet = gs.create_worksheet(
                    nf.WORKSHEET_TAB_BULK_SERVICES_TAB_MESSAGES
                )
                logger.info("Worksheet 'Messages' Created")
                bs_name = bs_row_data[nf.NF_INDEX_NAME]
                logger.info(f"Matching Bulk Service Name.. : {bs_name}")

                # Get All rows that matches the bulk service name in Messages sheet tab
                messages_rows = gs.get_rows_by_name(messages_worksheet, bs_name)
                logger.info(f"Message rows to be Updated: {messages_rows}")
                # Loop to update cells for each row
                if len(messages_rows) != 0:
                    logger.info("Updating worksheet using rows..")
                    for row in messages_rows:
                        gs.update_row(
                            row,
                            nf.COLUMN_MESSAGES_SERVICE_ID,
                            messages_worksheet,
                            bs_service_id,
                        )
                        logger.info(
                            f"Messages Row: {row} Updated With Service Id: {bs_service_id}"
                        )
                else:
                    logger.info("No 'Messages' row to update..")

            except Exception as e:
                error_msg = f"An error has occurred while updating 'Messages' sheet tab\n ERROR: {e}"

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
        wd.stop_process()


# Function to Define Gyro Command
def create_gyro_command(command_string, bs_service_id, wd):
    try:
        logger.info("STARTING GYRO COMMAND PROCESS")

        # Declare variable
        url = get_env_variable("WEBTOOL_GYRO_COMMAND_ADD_FULL_URL")
        array_command = command_string.split(", ")

        # Loop array command values
        for command_value in array_command:

            # Redirect to Gyro Command Add page
            logger.info("Redirecting to Gyro Command Add Page...")
            wd.redirect_to_page(url)

            logger.info(f"Adding Gyro Command: {command_value}")

            # Input Command Field
            wd.perform_action("name", nf.GYRO_COMMAND_FIELD, "sendkeys", command_value)

            # Choose Current Bulk Service - Service ID
            wd.perform_action(
                "xpath",
                f"//select[@name='svc_id']//option[@value='{bs_service_id}']",
                "click",
            )

            # Click Add button
            logger.info("Saving gyro command...")
            wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
            # .wait_until_element("xpath", nf.NF_SUCCESS_MESSAGE, "visible")
            logger.info(
                f"Gyro Command '{command_value}' Successfully Created - For Service ID: {bs_service_id}"
            )

    except Exception as e:
        logger.info(f"An error has occurred while defining gyro command\nERROR: {e}")
        wd.stop_process()
