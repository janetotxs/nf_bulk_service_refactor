from utils.logger import setup_logger
from utils.logger2 import logger
from nf.step_type_services import step_standard_flow as st
from nf import flow_service as flow
from nf.nf_constants import NfConstants

# logger = setup_logger(service_name=f"NF {__name__}")

# Call Constants
nf = NfConstants()


# Function to start Steps service loop using BS successfully created rows/row
def nf_start_service_steps(bs_worksheet, bs_success_rows, webdriver, gsheet):
    global wd
    global gs

    wd = webdriver
    gs = gsheet

    # Start looping all the bulk service success rows for 'Steps and Flow Construct' process
    for row in bs_success_rows:
        try:
            bs_row_data = bs_worksheet.row_values(row)
            logger.info(f"Bulk Service Data Row {row}: {bs_row_data}")

            # Create worksheet for ParamMatrix
            param_worksheet = gs.create_worksheet(
                nf.WORKSHEET_TAB_BULK_SERVICES_TAB_PARAM_MATRIX
            )

            # Start NF Service Step type process and return dictionary step details
            step_type_data = nf_start_steps_flow_construct(
                bs_row_data, param_worksheet, row
            )

            # Start Flow Process to Define Flow from 'step_from' to 'step_to'
            flow.nf_start_service_flows(
                step_type_data,
                bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT],
                bs_row_data[nf.NF_INDEX_SERVICE_ID],
                bs_worksheet,
                wd,
                gs,
                row,
            )

        except Exception as e:
            error_msg = f"An error has occurred on 'start_nf_service_steps' function\n ERROR: {e}"
            logger.info(error_msg)
            gs.update_rpa_remarks_error(row, error_msg)
            continue


# Funcion to handle/to determine what step and flow construct to execute
def nf_start_steps_flow_construct(bs_row_data, param_worksheet, row):
    # --------------------START STEP PROCESS------------------------#
    logger.info("STARTING PROCESS FOR: ADD SERVICE STEPS")
    # Assign BS Service Id to variable 'bs_service_id'
    bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
    steps_id = None
    try:

        logger.info(
            f"STARTING DEFINING STEPS FOR: {bs_service_id} = {bs_row_data[nf.NF_INDEX_NAME]}"
        )

        # Determine what specific process to defining steps and flows for bulk services.
        # Execute Process For Step Type = Prepaid CTL With Data
        logger.info(
            f"Steps and Flow Construct - Executing Process => '{bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]}'"
        )

        # Calling function to execute step type services for Prepaid CTL
        if "prepaid ctl" in bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT].lower():

            step_type_data = st.sf_construct_prepaid_ctl(
                bs_service_id, bs_row_data, param_worksheet, wd, gs
            )

            return step_type_data

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
        gs.update_rpa_remarks_error(row, error_msg)
        logger.info("Terminating Bot")
        wd.stop_process()
