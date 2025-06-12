from utils.env_loader import get_env_variable
from utils.logger2 import logger
from nf.nf_constants import NfConstants

# Call Constants
nf = NfConstants()


# Function to define the Service Expiry of Bulk Services
def create_service_expiry(bs_row_data, service_id, wd, gs):
    try:
        logger.info("STARTING EXPIRY SERVICE PROCESS")
        # Declare ParamMatrix Worksheet
        param_worksheet = gs.create_worksheet(
            nf.WORKSHEET_TAB_BULK_SERVICES_TAB_PARAM_MATRIX
        )

        # Declare Default Duration in days
        default_duration_in_days_value = bs_row_data[
            nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS
        ].lower()
        logger.info("Redirecting to Add Service Expiry Page")
        wd.driver.get(
            f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=service_expiries&op=add&details_id={service_id}"
        )
        wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "visible")

        # Section to Input Default Values
        # If Default Duration in Days value is No Expiry, choose radio button no expiry, else, multiple by 24
        logger.info("Page Successfully Reached! Creating Service Expiry...")
        if "no" in default_duration_in_days_value:
            wd.perform_action("id", "et_2", "click")
        else:
            # Input Expiry Field
            wd.perform_action(
                "id",
                "expiry",
                "sendkeys",
                int(default_duration_in_days_value) * 24,
            )

        # Click Add button
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
        logger.info("Service Expiry Created with Default Values")

        # Section to Input Param Matrix Values
        param_matrix_rows = gs.get_rows_by_name(
            param_worksheet, bs_row_data[nf.NF_INDEX_NAME]
        )

        if len(param_matrix_rows) != 0:
            for row in param_matrix_rows:
                param_matrix_data = param_worksheet.row_values(row)

                # Clear Input Param Field
                wd.perform_action("name", nf.SERVICE_PARAM_INPUT, "clear")

                # Input Param Field
                wd.perform_action(
                    "name",
                    nf.SERVICE_PARAM_INPUT,
                    "sendkeys",
                    param_matrix_data[nf.INDEX_PARAM_MATRIX_AMOUNT],
                )

                # Input Expiry
                wd.perform_action(
                    "id",
                    "expiry",
                    "sendkeys",
                    int(param_matrix_data[nf.INDEX_PARAM_MATRIX_DURATION]) * 24,
                )

                # Click Add button
                wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
                logger.info(
                    f"Service Expiry Created with ParamMatrix Values: {param_matrix_data[nf.INDEX_PARAM_MATRIX_PARAM]}"
                )

        else:
            logger.info("No Param Matrix Found for this Service name.")

    except Exception as e:
        logger.info(
            f"An error has occurred on function 'nf_add_service_expiry'\nERROR: {e}"
        )
        wd.stop_process()
