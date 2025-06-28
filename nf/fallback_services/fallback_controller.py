from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from utils.env_loader import get_env_variable
from utils.helpers import get_after_word, convert_string_hashmap
from utils.logger2 import logger
from nf.main_services.expiry_service import ExpiryService
from nf.main_services.step_type_service import StepTypeService
from nf.nf_constants import NfConstants
from utils.exceptions import (
    BulkServiceError,
    WalletError,
    GSheetUpdateError,
    ExpiryServiceError,
)
import time

# Constants
nf = NfConstants()


class FallbackController:
    def __init__(self, webdriver, gsheet, worksheets):
        self.wd = webdriver
        self.gs = gsheet
        self.worksheets = worksheets
        self.bs_current_row = None
        self.row_data = None
        self.step = None

    def start_nf_fallback_service(self):
        try:
            logger.info("STARTING FAILED SERVICE...")
            pending_rows = self.gs.get_pending_rows(
                self.worksheets["bulkService"],
                nf.COLUMN_BULK_SERVICE_DEPLOYMENT_DATE,
                nf.BS_INDEX_RPA_REMARKS_BASE_FLOW,
                "failed",
            )
            # If there's no current date today or failed status to work on, terminate script
            if not pending_rows:
                logger.warning(
                    "There's no current date to check failed services, terminating bot..."
                )
                self.wd.stop_process()
                # return []

            # Start looping pending rows
            for row in pending_rows:
                self.bs_current_row = row
                self.start_fail_controller(row)

        except Exception as e:
            logger.info(f"Unexpected error has occurred: {e}")

    def start_fail_controller(self, row):
        try:
            self.row_data = self.worksheets["bulkService"].row_values(row)
            bs_service_id = self.row_data[nf.NF_INDEX_SERVICE_ID]
            url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
            step = StepTypeService(self.wd, self.gs, url)
            self.step = step

            # Start looping using RPA remark range
            for i in range(nf.BS_INDEX_RPA_REMARKS_BULK_SERVICE, len(self.row_data)):

                # Decleare logic flow if its a base, double, extend, keyword or aux flow
                # 29 = RPA BULK SERVICE FLOW
                # 30 = RPA BASE FLOW
                # 31 = RPA DOUBLE FLOW
                # 32 = RPA EXTEND FLOW
                # 33 = KEYWORD SERVICE
                # 34 = AUX FLOW
                logic_flow = (
                    "aux"
                    if i == 34
                    else (
                        "keyword service"
                        if i == 33
                        else (
                            "extend"
                            if i == 32
                            else (
                                "double"
                                if i == 31
                                else "base" if i == 30 else "bulk service"
                            )
                        )
                    )
                )

                rpa_remarks_value = self.row_data[i]
                logger.info(f"Checking RPA Remark => {rpa_remarks_value}")
                # If rpa remark value is null or has no failed service, proceed to next loop
                if not rpa_remarks_value:
                    logger.info("RPA remark value has no value")
                    continue
                elif not "failed" in rpa_remarks_value.lower():
                    logger.info("RPA remark has no failed service")
                    continue

                dict_rpa_remark = convert_string_hashmap(rpa_remarks_value, "dict")
                print(dict_rpa_remark)
                # Start loop using RPA remarks dictionary
                # Section to create all failed step types
                step_type_data = {}
                logger.info("Checking each service status...")
                for key, value in dict_rpa_remark.items():
                    logger.info(f"{key} = {value}")
                    if value.lower() == "failed":
                        logger.info(f"{key} = {value} <- FOUND!")
                        step_data = self.process_failed_step_type(
                            dict_rpa_remark, logic_flow, key
                        )
                        step_type_data.update(step_data)

                # Section to define remaining steps to flow path

        except Exception as e:
            logger.info(f"Something went wrong with fail controller \nERROR: {e}")

    def process_failed_step_type2(self, dict_rpa_remark, logic_flow, step_type):
        try:
            logger.info(
                f"Processing fallback for Step Type: {step_type.upper()} - Logic Flow: {logic_flow.upper()} FLOW"
            )

            # AUX flow section
            if logic_flow == "aux":
                logger.info(f"Creating Step Type => Aux Flow - {step_type.upper()}")
                "TODO"
                # Call helper convert to string then update gsheet update row

            # Extend flow section
            elif logic_flow == "extend":
                flow_name = "EXTEND_PROVISION"
                logger.info(f"Creating Step Type => Extend Flow - {step_type.upper()}")
                "TODO"

            # Double flow section
            elif logic_flow == "double":
                flow_name = "DOUBLE_PROVISION"
                logger.info(f"Creating Step Type => Double Flow - {step_type.upper()}")
                "TODO"

            # Base flow section
            elif logic_flow == "base":
                flow_name = "PROVISION"
                logger.info(f"Creating Step Type => Base Flow - {step_type.upper()}")

                # For Step IN CHARGE Creation
                if "charge" in step_type.lower():
                    in_charge_data = self.step.step_type_in_charge(
                        logic_flow, self.row_data, self.worksheets["paramMatrix"]
                    )
                    dict_rpa_remark[step_type] = "Success"
                elif "extend_first_expiry" in step_type.lower():
                    "TODO"
                elif "data" in step_type.lower():
                    "TODO"
                elif "sms" in step_type.lower():
                    "TODO"
                elif "voice" in step_type.lower():
                    "TODO"
                elif "hlr" in step_type.lower():
                    "TODO"

        except TypeError as e:
            logger.info(f"Caught Exception: {e}")

        except Exception as e:
            logger.info(f"Something went wrong while checking the step types: {e}")
            raise

    def process_failed_step_type(self, dict_rpa_remark, logic_flow, step_type):
        try:
            logger.info("Executing Fallback => Step Type Process Creation")
            bs_service_id = self.row_data[nf.NF_INDEX_SERVICE_ID]
            logger.info(
                f"Processing fallback for Step Type: {step_type.upper()} - Logic Flow: {logic_flow.upper()} FLOW"
            )

            flow_name = (
                "DOUBLE_PROVISION"
                if logic_flow == "double"
                else "EXTEND_PROVISION" if logic_flow == "extend" else "PROVISION"
            )
            logger.info(
                f"Creating Step Type => {logic_flow.upper()} FLOW - {step_type.upper()}"
            )

            # For Step IN CHARGE Creation
            if "charge" in step_type.lower():
                in_charge_data = self.step.step_type_in_charge(
                    logic_flow, self.row_data, self.worksheets["paramMatrix"]
                )
                dict_rpa_remark[step_type] = "Success"

            # For Step EXTEND FIRST EXPIRY Creation
            elif "extend_first_expiry" in step_type.lower():
                extend_first_expiry_data = self.step.step_type_extend_first_expiry(
                    logic_flow,
                    bs_service_id,
                    self.row_data,
                    self.worksheets["paramMatrix"],
                )
                dict_rpa_remark[step_type] = "Success"

            # For Step DATA Creation
            elif "data" in step_type.lower():
                # For extend flow - execute function step_type_data_extend_wallet_expiry
                if logic_flow == "extend":
                    data_volume_bulk_data = (
                        self.step.step_type_data_extend_wallet_expiry(
                            bs_service_id, self.row_data
                        )
                    )
                    dict_rpa_remark[step_type] = "Success"
                # For standard or double flow - execute function step_type_data_prov_process
                else:
                    data_volume_bulk_data = self.step.step_type_data_prov_process(
                        logic_flow,
                        bs_service_id,
                        self.row_data,
                        self.worksheets["paramMatrix"],
                    )
                    dict_rpa_remark[step_type] = "Success"

            # For Step SMS or VOICE Creation
            elif "sms" in step_type.lower() or "voice" in step_type.lower():
                # Conditions to execute Step Type IN PROV SERVICE/IN ADD WALLET FUP/IN EXTEND WALLET EXPIRY
                if logic_flow == "double":
                    logger.info("Processing IN ADD WALLET FUP")
                    sms_voice_data = self.step.step_type_in_add_wallet_fup(
                        logic_flow, bs_service_id, self.row_data
                    )
                    dict_rpa_remark[step_type] = "Success"

                elif logic_flow == "extend":
                    logger.info("Processing IN EXTEND WALLET EXPIRY")
                    sms_voice_data = self.step.step_type_in_extend_wallet_expiry(
                        bs_service_id, self.row_data
                    )
                    dict_rpa_remark[step_type] = "Success"
                else:
                    # Execute Step Type Process = IN PROV SERVICE - UNLI SMS and/or IN PROV SERVICE - UNLI VOICE
                    logger.info("Processing IN PROV SERVICE")
                    sms_voice_data = self.step.step_type_in_prov_service(
                        logic_flow, bs_service_id, self.row_data
                    )
                    dict_rpa_remark[step_type] = "Success"

        except TypeError as e:
            logger.info(f"Caught Exception: {e}")
            dict_rpa_remark[step_type] = "Fallback Failed, Please check Input"
            pass

        except Exception as e:
            logger.info(f"Something went wrong while checking the step types: {e}")
            raise

    def process_failed_keyword(self, dict_rpa_remark, logic_flow, keyword):
        try:
            logger.info("Executing Fallback => Keyword Process Creation")
            keyword_type = keyword.lower()
            logger.info(
                f"Processing fallback for Keyword Service: {keyword_type.upper()}"
            )

            # AUX flow section
            if logic_flow == "extend":
                logger.info(f"Creating Step Type => Aux Flow - {keyword_type.upper()}")
                "TODO"
                # Call helper convert to string then update gsheet update row

            # Extend flow section
            elif keyword_type == "status":
                flow_name = "EXTEND_PROVISION"
                logger.info(
                    f"Creating Step Type => Extend Flow - {keyword_type.upper()}"
                )
                "TODO"

            # Double flow section
            elif keyword_type == "deprovision":
                flow_name = "DOUBLE_PROVISION"
                logger.info(
                    f"Creating Step Type => Double Flow - {keyword_type.upper()}"
                )
                "TODO"

            # Base flow section
            elif keyword_type == "provision":
                logger.info(f"Creating Step Type => Base Flow - {keyword_type.upper()}")
                flow_name = "PROVISION"
                # For Step IN CHARGE Creation
                if "charge" in keyword_type.lower():
                    in_charge_data = self.step.step_type_in_charge(
                        logic_flow, self.row_data, self.worksheets["paramMatrix"]
                    )
                    dict_rpa_remark[keyword_type] = "Success"
                    return in_charge_data

        except Exception as e:
            logger.info(f"Something went wrong while checking the step types: {e}")
            raise
