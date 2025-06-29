from utils.logger2 import logger
from utils.helpers import convert_string_hashmap
from nf.nf_constants import NfConstants
from nf.main_services.step_type_service import StepTypeService

# Call Constants and StepType Class
nf = NfConstants()


class PrepaidService:
    def __init__(self, webdriver, gsheet, worksheets):
        self.wd = webdriver
        self.gs = gsheet
        self.worksheets = worksheets
        self.dict_step_type_data = {}
        self.dict_incharge_extend_data = {}
        self.st = StepTypeService(webdriver, gsheet, worksheets)

    # Function to start Step and Flow Construct Process for Prepaid CTL
    def start_prepaid_process(
        self,
        double_extend_value,
        old_extend_step_id,
        bs_service_id,
        bs_row_data,
        param_worksheet,
        row,
    ):
        try:

            # Declare variables
            step_flow_construct_value = bs_row_data[
                nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT
            ].lower()

            rpa_column = (
                nf.COLUMN_BULK_SERVICE_RPA_REMARKS_EXTEND_FLOW
                if double_extend_value == "extend"
                else (
                    nf.COLUMN_BULK_SERVICE_RPA_REMARKS_DOUBLE_FLOW
                    if double_extend_value == "double"
                    else nf.COLUMN_BULK_SERVICE_RPA_REMARKS_BASE_FLOW
                )
            )
            # Initial setup of step type service
            self.st.initial_setup(row, double_extend_value, bs_row_data, bs_service_id)

            # =======================IN CHARGE and EXTEND FIRST EXPIRY FLOW SECTION=============================#
            # Execute Step Type Process = IN CHARGE
            if (
                "prepaid ctl" in step_flow_construct_value
                and double_extend_value != "double"
                or "prepaid opm" in step_flow_construct_value
                and double_extend_value == "extend"
            ):
                try:
                    in_charge_data = self.st.step_type_in_charge(param_worksheet)
                    self.dict_step_type_data.update(in_charge_data)

                    if double_extend_value != "extend":
                        self.dict_incharge_extend_data.update(in_charge_data)
                except TypeError:
                    logger.info(
                        "Returned object is empty => in_charge_data, proceed to next step type.."
                    )
                    # UPDATE RPA REMARK HERE FOR FAILED CREATION
                    pass
            else:
                logger.info("Skipping IN CHARGE - No creation needed for this Flow")

            if double_extend_value != "double":
                try:
                    # Execute Step Type Process = EXTEND FIRST EXPIRY
                    extend_first_expiry_data = self.st.step_type_extend_first_expiry(
                        bs_service_id,
                        param_worksheet,
                        old_extend_step_id,
                    )
                    self.dict_step_type_data.update(extend_first_expiry_data)
                    self.dict_incharge_extend_data.update(extend_first_expiry_data)
                except TypeError:
                    logger.info(
                        "Returned object is empty => extend_first_expiry_data, proceed to next step type.."
                    )
                    # UPDATE RPA REMARK HERE FOR FAILED CREATION
                    pass

            else:
                logger.info(
                    "Skipping EXTEND FIRST EXPIRY - No creation needed for this Flow"
                )

            # =====================Data - DATA PROV WITH KEYWORD MAPPING, DATA PROV EXTENSION WITH KEYWORD MAPPING================#
            # =====================and DATA EXTEND WALLET EXPIRY FLOW SECTION=====================================================#
            # If there's a 'data' keyword in Step and Flow Construct value, execute this section
            if "data" in step_flow_construct_value:
                try:
                    # For extend flow - execute function step_type_data_extend_wallet_expiry
                    if double_extend_value == "extend":
                        data_volume_bulk_data = (
                            self.st.step_type_data_extend_wallet_expiry(bs_service_id)
                        )
                        self.dict_step_type_data.update(data_volume_bulk_data)
                    # For standard or double flow - execute function step_type_data_prov_process
                    else:
                        data_volume_bulk_data = self.st.step_type_data_prov_process(
                            bs_service_id,
                            param_worksheet,
                        )
                        self.dict_step_type_data.update(data_volume_bulk_data)
                except TypeError:
                    logger.info(
                        "Returned object is empty => data_volume_bulk_data, proceed to next step type.."
                    )
                    # UPDATE RPA REMARK HERE FOR FAILED CREATION
                    pass

            else:
                logger.info(
                    "Skipping step type DATA - No creation needed for this Flow"
                )

            # =====================Unli SMS/Unli Voice - IN PROV SERVICE, IN ADD WALLET FUP=======================#
            # =====================and IN EXTEND WALLET EXPIRY FLOW SECTION=======================================#
            # If there's a 'Unli SMS' or 'Unli Voice' keyword in Step and Flow Construct value, execute this section: IN PROV SERVICE - UNLI SMS or IN PROV SERVICE - UNLI VOICE
            if (
                "unli sms" in step_flow_construct_value
                or "unli voice" in step_flow_construct_value
            ):
                try:
                    # Conditions to execute Step Type IN PROV SERVICE/IN ADD WALLET FUP/IN EXTEND WALLET EXPIRY
                    if double_extend_value == "double":
                        logger.info("Processing IN ADD WALLET FUP")
                        sms_voice_data = self.st.step_type_in_add_wallet_fup(
                            bs_service_id
                        )
                        self.dict_step_type_data.update(sms_voice_data)

                    elif double_extend_value == "extend":
                        logger.info("Processing IN EXTEND WALLET EXPIRY")
                        sms_voice_data = self.st.step_type_in_extend_wallet_expiry(
                            bs_service_id
                        )
                        self.dict_step_type_data.update(sms_voice_data)

                    else:
                        # Execute Step Type Process = IN PROV SERVICE - UNLI SMS and/or IN PROV SERVICE - UNLI VOICE
                        logger.info("Processing IN PROV SERVICE")
                        sms_voice_data = self.st.step_type_in_prov_service(
                            bs_service_id
                        )
                        self.dict_step_type_data.update(sms_voice_data)
                except TypeError:
                    logger.info(
                        "Returned object is empty => sms_voice_data, proceed to next step.."
                    )
                    # UPDATE RPA REMARK HERE FOR FAILED CREATION
                    pass
            else:
                logger.info(
                    "Skipping step type Unli SMS or VOICE - No creation needed for this Flow"
                )

            # =====================Unli Voice - HLR - PLYF LOW SECTION=======================#
            # Conditions to execute HLR PLY Step Type if there's a Unli Voice in Step and Flow Construct Value
            try:
                if (
                    "unli voice" in step_flow_construct_value
                    and double_extend_value != "double"
                    and double_extend_value != "extend"
                ):

                    # Execute Step Type Process = HLR PLY
                    logger.info("Processing HLR - PLY")
                    hlr_ply_data = self.st.step_type_hlr_ply(bs_service_id)
                    self.dict_step_type_data.update(hlr_ply_data)
                    self.dict_incharge_extend_data.update(hlr_ply_data)

                else:
                    logger.info("Skipping HLR PLY - No creation needed for this Flow")

            except TypeError:
                logger.info(
                    "Returned object is empty => hlr_ply_data, proceed to next step.."
                )
                # UPDATE RPA REMARK HERE FOR FAILED CREATION
                pass

            logger.info(
                f"Successfully Retreived Step Type Data: {self.dict_step_type_data}"
            )
            # logger.info(f"Old Data: {self.dict_incharge_extend_data}")

            # Update Bulk Service RPA Remarks
            try:

                if not self.st.bs_rpa_remark_fail:
                    logger.info("Updating Worksheet - Bulk Service RPA Remark")
                    self.gs.update_row(
                        row, rpa_column, self.worksheets["bulkService"], "Success"
                    )
                else:
                    # Convert failed remarks from dictionary to string
                    bs_rpa_remark_string = convert_string_hashmap(
                        self.st.bs_rpa_remark_fail, "string"
                    )
                    print(f"Check Bulk RPA Remark Fail: {bs_rpa_remark_string}")
                    self.gs.update_row(
                        row,
                        rpa_column,
                        self.worksheets["bulkService"],
                        bs_rpa_remark_string,
                    )
            except Exception as e:
                logger.info(
                    f"Unexpected error while updating Bulk Service RPA Remark\nERROR: {e}"
                )

            # Update ParamMatrix RPA Remarks
            try:
                if self.st.param_rows:
                    logger.info("Updating Worksheet - ParamMatrix RPA Remark")
                    if not self.st.param_rpa_remark_fail:
                        for param_row in self.st.param_rows:
                            print(
                                f"{param_row} ==== {nf.COLUMN_PARAM_MATRIX_RPA_REMARKS}"
                            )
                            print(self.worksheets["paramMatrix"].col_count)
                            self.gs.update_row(
                                param_row,
                                nf.COLUMN_PARAM_MATRIX_RPA_REMARKS,
                                self.worksheets["paramMatrix"],
                                "Param Successfully Defined",
                            )
                    else:
                        # Convert failed remarks from dictionary to string
                        param_rpa_remark_string = convert_string_hashmap(
                            self.st.param_rpa_remark_fail, "string"
                        )
                        print(f"Check Param RPA Remark Fail: {param_rpa_remark_string}")
                        for param_row in self.st.param_rows:
                            print(
                                f"{param_row} ==== {nf.COLUMN_PARAM_MATRIX_RPA_REMARKS}"
                            )
                            print(self.worksheets["paramMatrix"].col_count)
                            self.gs.update_row(
                                param_row,
                                nf.COLUMN_PARAM_MATRIX_RPA_REMARKS,
                                self.worksheets["paramMatrix"],
                                param_rpa_remark_string,
                            )
                else:
                    logger.info("No ParamMatrix Remark to Update")

            except Exception as e:
                logger.info(
                    f"Unexpected error while updating ParamMatrix RPA Remark\nERROR: {e}"
                )

            return self.dict_step_type_data, self.dict_incharge_extend_data

        except Exception as e:
            logger.info(f"Something went wrong on prepaid service process\nERROR: {e}")
            raise
