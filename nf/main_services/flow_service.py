from selenium.webdriver.common.by import By
from utils.env_loader import get_env_variable
from utils.logger2 import logger
from nf.main_services import bulk_service as bs
from nf.nf_constants import NfConstants
from nf.main_services.bulk_service import BulkServices

# logger = setup_logger(service_name=f"NF {__name__}")

# Call Constants
nf = NfConstants()


class FlowService:
    def __init__(self, worksheets, webdriver, gsheet):
        self.wd = webdriver
        self.gs = gsheet
        self.worksheets = worksheets
        self.bs = BulkServices(worksheets, webdriver, gsheet)

    # Function to Start Service Flow Process
    def nf_start_service_flows(
        self,
        double_extend_value,
        step_type_data,
        bs_row,
    ):
        # --------------------START FLOWS PROCESS------------------------#
        try:
            # Create Worksheet once againa for bulk service sheet to get updated value rpa remarks
            bs_row_data = self.worksheets["bulkService"].row_values(bs_row)

            # Declare Variables
            step_flow_construct_value = bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]
            bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]

            logger.info(f"STARTING FLOW CREATION PROCESS")

            # Redirect to Add Service Flow Page
            url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=flows&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
            self.wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)
            self.wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

            # Execute Flow process based on Step and Flow construct
            # Check if step and flow construct value has keyword of 'prepaid ctl'
            if "prepaid ctl" in step_flow_construct_value.lower():
                self.create_flow_prepaid_ctl(
                    double_extend_value,
                    step_type_data,
                    bs_row_data,
                    bs_row,
                )

            # Check if step and flow construct value has keyword of 'prepaid opm'
            elif "prepaid opm" in step_flow_construct_value.lower():
                self.create_flow_prepaid_opm(
                    double_extend_value,
                    step_type_data,
                    bs_row_data,
                    bs_row,
                )

        except Exception as e:
            error_msg = f"Something went wrong in the Process Sequence of 'SERVICE FLOW PROCESS'.\nERROR: {e}"
            logger.info(error_msg)
            raise
            # --------------------END FLOWS PROCESS------------------------#

    # Function to Execute Flow process Specifically for Prepaid CTL With Data
    def create_flow_prepaid_ctl(
        self,
        double_extend_value,
        step_type_data,
        bs_row_data,
        bs_row,
    ):

        # Declare Variables
        step_flow_construct_value = bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]
        bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
        flow_name = (
            "DOUBLE_PROVISION"
            if double_extend_value == "double"
            else (
                "EXTEND_PROVISION" if double_extend_value == "extend" else "PROVISION"
            )
        )
        flow_id = None

        logger.info(f"Defining Flow for {step_flow_construct_value}")

        # Input Step Name Field
        self.wd.perform_action("name", nf.NF_FLOWS_NAME_INPUT, "sendkeys", flow_name)

        # Dropdown First Step Field
        self.wd.perform_action(
            "xpath",
            f"//select[@name='first_step_id']//option[@value='{step_type_data['in_charge_id']}' and contains(text(), '{step_type_data['in_charge_name']}')]",
            "click",
        )

        # Click 'Add' Button
        self.wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
        logger.info("SERVICE FLOW SUCCESSFULLY CREATED!")

        # FOR TEST ONLY redirect to flow edit page
        # self.wd.driver.get(
        #    "http://10.47.69.195/nf/index.php?mod=flows&op=details&id=5039"
        # )

        # Get Unique Flow ID from div element page under Flow Details.
        current_link = self.wd.driver.current_url

        flow_id_element = (
            nf.FLOW_ID_PROD if "10.25" in current_link else nf.FLOW_ID_TESTBED
        )

        self.wd.wait_until_element("xpath", flow_id_element, "visible")
        flow_id = self.wd.driver.find_element(By.XPATH, flow_id_element).text
        logger.info(f"Flow ID Retrieved: {flow_id}")
        self.wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

        try:
            # Define step from IN CHARGE to EXTENDS FIRST EXPIRY
            self.define_stepfrom_stepto(
                step_type_data["in_charge_id"],
                step_type_data["in_charge_name"],
                step_type_data["extend_first_expiry_id"],
                step_type_data["extend_first_expiry_name"],
            )
        except KeyError as e:
            logger.info(
                f"KeyError, key does not exist: {e} - Skipping 'from IN CHARGE to EXTENDS FIRST EXPIRY'"
            )

        # Determine what Flow to be executed based on Step and Flow Construct
        # Condition for Prepaid CTL with Data, Unli SMS and Unli Voice
        sf_construct_value = step_flow_construct_value.lower()

        try:
            if sf_construct_value == "prepaid ctl with data, unli sms and unli voice":
                try:
                    # Define step from EXTENDS FIRST EXPIRY to DATA PROV WITH KEYWORD MAPPING
                    self.define_stepfrom_stepto(
                        step_type_data["extend_first_expiry_id"],
                        step_type_data["extend_first_expiry_name"],
                        step_type_data["data_prov_id"],
                        step_type_data["data_prov_name"],
                    )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping from 'from EXTENDS FIRST EXPIRY to DATA PROV WITH KEYWORD MAPPING'"
                    )
                    pass

                try:
                    # Define step from DATA PROV WITH KEYWORD MAPPING to IN PROV SERVICE - Unli SMS
                    self.define_stepfrom_stepto(
                        step_type_data["data_prov_id"],
                        step_type_data["data_prov_name"],
                        step_type_data["unli_sms_id"],
                        step_type_data["unli_sms_name"],
                    )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping from 'from DATA PROV WITH KEYWORD MAPPING to IN PROV SERVICE - Unli SMS"
                    )
                    pass

                try:
                    # Define step from IN PROV SERVICE - Unli SMS to IN PROV SERVICE - Unli Voice
                    self.define_stepfrom_stepto(
                        step_type_data["unli_sms_id"],
                        step_type_data["unli_sms_name"],
                        step_type_data["unli_voice_id"],
                        step_type_data["unli_voice_name"],
                    )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping from 'from IN PROV SERVICE - Unli SMS to IN PROV SERVICE - Unli Voice"
                    )
                    pass

                try:
                    # Define step from IN PROV SERVICE - Unli VOICE to HLR PLY
                    if (
                        double_extend_value != "double"
                        and double_extend_value != "extend"
                    ):
                        self.define_stepfrom_stepto(
                            step_type_data["unli_voice_id"],
                            step_type_data["unli_voice_name"],
                            step_type_data["hlr_ply_id"],
                            step_type_data["hlr_ply_name"],
                        )

                    logger.info(
                        "FLOW SUCCESSFULLY DEFINED FOR = Prepaid CTL With Data, Unli SMS and Unli Voice"
                    )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping 'from IN PROV SERVICE - Unli VOICE to HLR PLY'"
                    )
                    pass
        except Exception as e:
            logger.info(
                f"An error has occurred while defining Flow of 'prepaid ctl with data, unli sms and unli voice': {e}"
            )

        try:
            # Condition for Prepaid CTL with Data and Unli SMS
            if sf_construct_value == "prepaid ctl with data and unli sms":
                try:
                    # Define step from EXTENDS FIRST EXPIRY to DATA PROV WITH KEYWORD MAPPING then update values to Flow worksheet calling self.gs.inser_new_row
                    self.define_stepfrom_stepto(
                        step_type_data["extend_first_expiry_id"],
                        step_type_data["extend_first_expiry_name"],
                        step_type_data["data_prov_id"],
                        step_type_data["data_prov_name"],
                    )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping 'from EXTENDS FIRST EXPIRY to DATA PROV WITH KEYWORD MAPPING'"
                    )
                    pass

                try:
                    # Define step from DATA PROV WITH KEYWORD MAPPING to IN PROV SERVICE - Unli SMS
                    self.define_stepfrom_stepto(
                        step_type_data["data_prov_id"],
                        step_type_data["data_prov_name"],
                        step_type_data["unli_sms_id"],
                        step_type_data["unli_sms_name"],
                    )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping 'from DATA PROV WITH KEYWORD MAPPING to IN PROV SERVICE'"
                    )
                    pass

                    logger.info(
                        "FLOW SUCCESSFULLY DEFINED FOR = Prepaid CTL With Data and Unli SMS"
                    )
        except Exception as e:
            logger.info(
                f"An error has occurred while defining Flow of 'prepaid ctl with data and unli sms': {e}"
            )
        try:
            # Condition for Prepaid CTL with Unli SMS and Unli Voice
            if sf_construct_value == "prepaid ctl with unli sms and unli voice":
                try:
                    # Define step from EXTENDS FIRST EXPIRY to IN PROV SERVICE - Unli SMS
                    self.define_stepfrom_stepto(
                        step_type_data["extend_first_expiry_id"],
                        step_type_data["extend_first_expiry_name"],
                        step_type_data["unli_sms_id"],
                        step_type_data["unli_sms_name"],
                    )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping 'from EXTENDS FIRST EXPIRY to IN PROV SERVICE - Unli SMS'"
                    )
                    pass
                try:
                    # Define step from IN PROV SERVICE - Unli SMS to IN PROV SERVICE - Unli Voice
                    self.define_stepfrom_stepto(
                        step_type_data["unli_sms_id"],
                        step_type_data["unli_sms_name"],
                        step_type_data["unli_voice_id"],
                        step_type_data["unli_voice_name"],
                    )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping 'from IN PROV SERVICE - Unli SMS to IN PROV SERVICE - Unli Voice'"
                    )
                    pass

                    # # Define step from IN PROV SERVICE - Unli VOICE to HLR PLY
                    # if (
                    #     double_extend_value != "double"
                    #     and double_extend_value != "extend"
                    # ):
                    #     self.define_stepfrom_stepto(
                    #         step_type_data["unli_voice_id"],
                    #         step_type_data["unli_voice_name"],
                    #         step_type_data["hlr_ply_id"],
                    #         step_type_data["hlr_ply_name"],
                    #     )

                    # logger.info(
                    #     "FLOW SUCCESSFULLY DEFINED FOR = Prepaid CTL With Unli SMS and Unli Voice"
                    # )
        except Exception as e:
            logger.info(
                f"An error has occurred while defining Flow of 'prepaid ctl with unli sms and unli voice': {e}"
            )
        try:
            # Condition for Prepaid CTL with Data
            if sf_construct_value == "prepaid ctl with data":
                try:
                    # Define step from EXTENDS FIRST EXPIRY to DATA PROV WITH KEYWORD MAPPIN
                    self.define_stepfrom_stepto(
                        step_type_data["extend_first_expiry_id"],
                        step_type_data["extend_first_expiry_name"],
                        step_type_data["data_prov_id"],
                        step_type_data["data_prov_name"],
                    )

                    logger.info("FLOW SUCCESSFULLY DEFINED FOR = Prepaid CTL With Data")
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping 'from EXTENDS FIRST EXPIRY to DATA PROV WITH KEYWORD MAPPIN'"
                    )
                    pass

        except Exception as e:
            logger.info(
                f"An error has occurred while defining Flow of 'prepaid ctl with data': {e}"
            )

        # Call Function from bulk_service to execute defining Default and API Flow of Bulk Services using flow ID and flow name
        self.bs.nf_assign_bulk_service_flow(double_extend_value, bs_service_id, flow_id)
        flow_string = (
            f"{'Base' if double_extend_value == '' else double_extend_value.upper()}"
        )

        logger.info(f"Bulk Service {flow_string} Flow and API Flow Updated")

    # Function to Execute Flow process Specifically for Prepaid CTL With Data
    def create_flow_prepaid_opm(
        self,
        double_extend_value,
        step_type_data,
        bs_row_data,
        bs_row,
    ):

        # Declare Variables
        step_flow_construct_value = bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]
        bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
        first_step_assign = (
            step_type_data["in_charge_id"]
            if double_extend_value == "extend"
            else step_type_data["extend_first_expiry_id"]
        )
        flow_name = (
            "DOUBLE_PROVISION"
            if double_extend_value == "double"
            else (
                "EXTEND_PROVISION" if double_extend_value == "extend" else "PROVISION"
            )
        )
        flow_id = None

        logger.info(f"Defining Flow for {step_flow_construct_value}")

        # Input Step Name Field
        self.wd.perform_action("name", nf.NF_FLOWS_NAME_INPUT, "sendkeys", flow_name)

        # Dropdown First Step Field
        self.wd.perform_action(
            "xpath",
            f"//select[@name='first_step_id']//option[@value='{first_step_assign}']",
            "click",
        )

        # Click 'Add' Button
        self.wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
        logger.info("SERVICE FLOW SUCCESSFULLY CREATED!")

        # FOR TEST ONLY redirect to flow edit page
        # self.wd.driver.get(
        #    "http://10.47.69.195/nf/index.php?mod=flows&op=details&id=5039"
        # )

        # Get Unique Flow ID from div element page under Flow Details.
        current_link = self.wd.driver.current_url

        flow_id_element = (
            nf.FLOW_ID_PROD if "10.25" in current_link else nf.FLOW_ID_TESTBED
        )

        self.wd.wait_until_element("xpath", flow_id_element, "visible")
        self.wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")
        flow_id = self.wd.driver.find_element(By.XPATH, flow_id_element).text
        logger.info(f"Flow ID Retrieved: {flow_id}")
        try:
            # Define step from IN CHARGE to EXTENDS FIRST EXPIRY for extend flow only
            if double_extend_value == "extend":
                self.define_stepfrom_stepto(
                    step_type_data["in_charge_id"],
                    step_type_data["in_charge_name"],
                    step_type_data["extend_first_expiry_id"],
                    step_type_data["extend_first_expiry_name"],
                )
        except KeyError as e:
            logger.info(
                f"KeyError, key does not exist: {e} - Skipping 'from IN CHARGE to EXTENDS FIRST EXPIRY'"
            )
        # Determine what Flow to be executed based on Step and Flow Construct
        # Condition for Prepaid CTL with Data, Unli SMS and Unli Voice
        sf_construct_value = step_flow_construct_value.lower()
        try:
            if sf_construct_value == "prepaid opm with data, unli sms and unli voice":
                try:
                    # Define step from EXTENDS FIRST EXPIRY to DATA PROV WITH KEYWORD MAPPING
                    self.define_stepfrom_stepto(
                        step_type_data["extend_first_expiry_id"],
                        step_type_data["extend_first_expiry_name"],
                        step_type_data["data_prov_id"],
                        step_type_data["data_prov_name"],
                    )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping 'from EXTENDS FIRST EXPIRY to DATA PROV WITH KEYWORD MAPPING'"
                    )
                    pass

                try:
                    # Define step from DATA PROV WITH KEYWORD MAPPING to IN PROV SERVICE - Unli SMS
                    self.define_stepfrom_stepto(
                        step_type_data["data_prov_id"],
                        step_type_data["data_prov_name"],
                        step_type_data["unli_sms_id"],
                        step_type_data["unli_sms_name"],
                    )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping 'from DATA PROV WITH KEYWORD MAPPING to IN PROV SERVICE - Unli SMS'"
                    )
                    pass

                try:
                    # Define step from IN PROV SERVICE - Unli SMS to IN PROV SERVICE - Unli Voice
                    self.define_stepfrom_stepto(
                        step_type_data["unli_sms_id"],
                        step_type_data["unli_sms_name"],
                        step_type_data["unli_voice_id"],
                        step_type_data["unli_voice_name"],
                    )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping 'from DATA PROV WITH KEYWORD MAPPING to IN PROV SERVICE - Unli SMS'"
                    )
                    pass
                try:
                    # Define step from IN PROV SERVICE - Unli VOICE to HLR PLY
                    if (
                        double_extend_value != "double"
                        and double_extend_value != "extend"
                    ):
                        self.define_stepfrom_stepto(
                            step_type_data["unli_voice_id"],
                            step_type_data["unli_voice_name"],
                            step_type_data["hlr_ply_id"],
                            step_type_data["hlr_ply_name"],
                        )
                        logger.info(
                            "FLOW SUCCESSFULLY DEFINED FOR = Prepaid OPM With Data, Unli SMS and Unli Voice"
                        )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping 'from DATA PROV WITH KEYWORD MAPPING to IN PROV SERVICE - Unli SMS'"
                    )

        except Exception as e:
            logger.info(
                f"An error has occurred while defining Flow of 'prepaid opm with data and unli sms': {e}"
            )
        try:
            # Condition for Prepaid CTL with Data and Unli SMS
            if sf_construct_value == "prepaid opm with data and unli sms":
                try:
                    # Define step from EXTENDS FIRST EXPIRY to DATA PROV WITH KEYWORD MAPPING
                    self.define_stepfrom_stepto(
                        step_type_data["extend_first_expiry_id"],
                        step_type_data["extend_first_expiry_name"],
                        step_type_data["data_prov_id"],
                        step_type_data["data_prov_name"],
                    )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping 'from EXTENDS FIRST EXPIRY to DATA PROV WITH KEYWORD MAPPING'"
                    )
                    pass
                try:
                    # Define step from DATA PROV WITH KEYWORD MAPPING to IN PROV SERVICE - Unli SMS
                    self.define_stepfrom_stepto(
                        step_type_data["data_prov_id"],
                        step_type_data["data_prov_name"],
                        step_type_data["unli_sms_id"],
                        step_type_data["unli_sms_name"],
                    )

                    logger.info(
                        "FLOW SUCCESSFULLY DEFINED FOR = Prepaid OPM With Data and Unli SMS"
                    )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping 'from EXTENDS FIRST EXPIRY to DATA PROV WITH KEYWORD MAPPING'"
                    )
                    pass

        except Exception as e:
            logger.info(
                f"An error has occurred while defining Flow of 'prepaid ctl with data and unli sms': {e}"
            )
        try:
            # Condition for Prepaid CTL with Unli SMS and Unli Voice
            if sf_construct_value == "prepaid opm with unli sms and unli voice":
                try:
                    # Define step from EXTENDS FIRST EXPIRY to IN PROV SERVICE - Unli SMS
                    self.define_stepfrom_stepto(
                        step_type_data["extend_first_expiry_id"],
                        step_type_data["extend_first_expiry_name"],
                        step_type_data["unli_sms_id"],
                        step_type_data["unli_sms_name"],
                    )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping 'from EXTENDS FIRST EXPIRY to IN PROV SERVICE - Unli SMS'"
                    )
                    pass
                    # Define step from IN PROV SERVICE - Unli SMS to IN PROV SERVICE - Unli Voice
                    self.define_stepfrom_stepto(
                        step_type_data["unli_sms_id"],
                        step_type_data["unli_sms_name"],
                        step_type_data["unli_voice_id"],
                        step_type_data["unli_voice_name"],
                    )
                try:
                    # Define step from IN PROV SERVICE - Unli VOICE to HLR PLY
                    if (
                        double_extend_value != "double"
                        and double_extend_value != "extend"
                    ):
                        self.define_stepfrom_stepto(
                            step_type_data["unli_voice_id"],
                            step_type_data["unli_voice_name"],
                            step_type_data["hlr_ply_id"],
                            step_type_data["hlr_ply_name"],
                        )
                        logger.info(
                            "FLOW SUCCESSFULLY DEFINED FOR = Prepaid OPM With Unli SMS and Unli Voice"
                        )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping 'from IN PROV SERVICE - Unli VOICE to HLR PLY'"
                    )
                    pass

        except Exception as e:
            logger.info(
                f"An error has occurred while defining Flow of 'prepaid opm with unli sms and unli voice': {e}"
            )
        try:
            # Condition for Prepaid CTL with Data
            if sf_construct_value == "prepaid opm with data":
                try:
                    # Define step from EXTENDS FIRST EXPIRY to DATA PROV WITH KEYWORD MAPPIN
                    self.define_stepfrom_stepto(
                        step_type_data["extend_first_expiry_id"],
                        step_type_data["extend_first_expiry_name"],
                        step_type_data["data_prov_id"],
                        step_type_data["data_prov_name"],
                    )
                    logger.info("FLOW SUCCESSFULLY DEFINED FOR = Prepaid OPM With Data")
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping 'from EXTENDS FIRST EXPIRY to DATA PROV WITH KEYWORD MAPPIN'"
                    )
                    pass

        except Exception as e:
            logger.info(
                f"An error has occurred while defining Flow of 'prepaid opm with data': {e}"
            )
        try:
            # Condition for Prepaid CTL with Unli SMS and Unli Voice
            if sf_construct_value == "prepaid opm with data and unli voice":
                try:
                    # Define step from EXTENDS FIRST EXPIRY to IN PROV SERVICE - Unli SMS
                    self.define_stepfrom_stepto(
                        step_type_data["extend_first_expiry_id"],
                        step_type_data["extend_first_expiry_name"],
                        step_type_data["data_prov_id"],
                        step_type_data["data_prov_name"],
                    )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping 'from EXTENDS FIRST EXPIRY to IN PROV SERVICE - Unli SMS'"
                    )
                    pass
                try:
                    # Define step from IN PROV SERVICE - Unli SMS to IN PROV SERVICE - Unli Voice
                    self.define_stepfrom_stepto(
                        step_type_data["data_prov_id"],
                        step_type_data["data_prov_name"],
                        step_type_data["unli_voice_id"],
                        step_type_data["unli_voice_name"],
                    )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping 'from IN PROV SERVICE - Unli SMS to IN PROV SERVICE - Unli Voice'"
                    )
                    pass

                try:
                    # Define step from IN PROV SERVICE - Unli VOICE to HLR PLY
                    if (
                        double_extend_value != "double"
                        and double_extend_value != "extend"
                    ):
                        self.define_stepfrom_stepto(
                            step_type_data["unli_voice_id"],
                            step_type_data["unli_voice_name"],
                            step_type_data["hlr_ply_id"],
                            step_type_data["hlr_ply_name"],
                        )

                        logger.info(
                            "FLOW SUCCESSFULLY DEFINED FOR = Prepaid OPM With Data and Unli Voice"
                        )
                except KeyError as e:
                    logger.info(
                        f"KeyError, key does not exist: {e} - Skipping 'from IN PROV SERVICE - Unli VOICE to HLR PLY'"
                    )
                    pass

        except Exception as e:
            logger.info(
                f"An error has occurred while defining Flow of 'prepaid data with data and unli voice': {e}"
            )

        # Call Function from bulk_service to execute defining Default and API Flow of Bulk Services using flow ID and flow name
        self.bs.nf_assign_bulk_service_flow(double_extend_value, bs_service_id, flow_id)
        flow_string = (
            f"{'Base' if double_extend_value == '' else double_extend_value.upper()}"
        )

        logger.info(f"Bulk Service {flow_string} Flow and API Flow Updated")

    def define_stepfrom_stepto(
        self, step_type_id_from, step_type_name_from, step_type_id_to, step_type_name_to
    ):
        try:
            logger.info(
                f"Assigning Flow - STEP FROM: {step_type_name_from} - STEP TO: {step_type_name_to}"
            )
            # Dropdown Step from Dropdown
            self.wd.perform_action(
                "xpath",
                f"//select[@name='step_id_from']//option[@value='{step_type_id_from}' and contains(text(), '{step_type_name_from}')]",
                "click",
            )

            # Dropdown Step to Dropdown
            self.wd.perform_action(
                "xpath",
                f"//select[@name='step_id_to']//option[@value='{step_type_id_to}' and contains(text(), '{step_type_name_to}')]",
                "click",
            )

            # Click 'Add' Button
            self.wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
            self.wd.wait_until_element(
                "xpath",
                f"//a[@href='index.php?mod=steps&op=details&id={step_type_id_to}']",
                "visible",
            )

            logger.info(
                f"Flow Successfully Added: From - {step_type_id_from} ({step_type_name_from}) To: {step_type_id_to} ({step_type_name_to}) Successfully Added"
            )
        except Exception as e:
            logger.info(
                f"Something went wrong in the function of 'define_stepfrom_stepto'\nERROR: {e}"
            )

    def define_stepfrom_stepto_fail(self, step_type_name_from, step_type_name_to):
        try:
            logger.info(
                f"Assigning Flow - STEP FROM: {step_type_name_from} - STEP TO: {step_type_name_to}"
            )
            # Dropdown Step from Dropdown
            self.wd.perform_action(
                "xpath",
                f"//select[@name='step_id_from']//option[contains(text(), '{step_type_name_from}')]",
                "click",
            )

            # Dropdown Step to Dropdown
            self.wd.perform_action(
                "xpath",
                f"//select[@name='step_id_from']//option[contains(text(), '{step_type_name_to}')]",
                "click",
            )

            # Click 'Add' Button
            self.wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
            self.wd.wait_until_element(
                "xpath",
                f"//td[@align='left']//a[contains(text(), '{step_type_name_from}')]']",
                "visible",
            )

            logger.info(
                f"Flow Successfully Added: From - ({step_type_name_from}) To: ({step_type_name_to}) Successfully Added"
            )
        except Exception as e:
            logger.info(
                f"Something went wrong in the function of 'define_stepfrom_stepto'\nERROR: {e}"
            )
