from utils.logger import setup_logger
from utils.env_loader import get_env_variable
from utils.logger2 import logger
from nf.nf_constants import NfConstants
from nf.main_services import step_and_flow_construct_service as sfc
from nf.main_services.step_type_service import StepTypeService

# Call Constants and StepType Class
nf = NfConstants()


# Function to start Step and Flow Construct Process for Prepaid CTL
def start_construct_prepaid(
    double_extend_value,
    old_extend_step_id,
    bs_service_id,
    bs_row_data,
    param_worksheet,
    webdriver,
    gsheet,
):
    try:

        # Declare empty dictionary
        dict_step_type_data = {}
        dict_incharge_extend_data = {}
        step_flow_construct_value = bs_row_data[
            nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT
        ].lower()

        url_step_page = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"

        # Instantiate StepType Class
        st = StepTypeService(webdriver, gsheet, url_step_page)

        # =======================IN CHARGE and EXTEND FIRST EXPIRY FLOW SECTION=============================#
        # Execute Step Type Process = IN CHARGE
        if (
            "prepaid ctl" in step_flow_construct_value
            and double_extend_value != "double"
            or "prepaid opm" in step_flow_construct_value
            and double_extend_value == "extend"
        ):
            try:
                in_charge_data = st.step_type_in_charge(
                    double_extend_value, bs_row_data, param_worksheet
                )
                dict_step_type_data.update(in_charge_data)

                if double_extend_value != "extend":
                    dict_incharge_extend_data.update(in_charge_data)
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
                extend_first_expiry_data = st.step_type_extend_first_expiry(
                    double_extend_value,
                    old_extend_step_id,
                    bs_service_id,
                    bs_row_data,
                    param_worksheet,
                )
                dict_step_type_data.update(extend_first_expiry_data)
                dict_incharge_extend_data.update(extend_first_expiry_data)
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
                    data_volume_bulk_data = st.step_type_data_extend_wallet_expiry(
                        bs_service_id, bs_row_data
                    )
                    dict_step_type_data.update(data_volume_bulk_data)
                # For standard or double flow - execute function step_type_data_prov_process
                else:
                    data_volume_bulk_data = st.step_type_data_prov_process(
                        double_extend_value, bs_service_id, bs_row_data, param_worksheet
                    )
                    dict_step_type_data.update(data_volume_bulk_data)
            except TypeError:
                logger.info(
                    "Returned object is empty => data_volume_bulk_data, proceed to next step type.."
                )
                # UPDATE RPA REMARK HERE FOR FAILED CREATION
                pass

        else:
            logger.info("Skipping step type DATA - No creation needed for this Flow")

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
                    sms_voice_data = st.step_type_in_add_wallet_fup(
                        double_extend_value, bs_service_id, bs_row_data
                    )
                    dict_step_type_data.update(sms_voice_data)

                elif double_extend_value == "extend":
                    logger.info("Processing IN EXTEND WALLET EXPIRY")
                    sms_voice_data = st.step_type_in_extend_wallet_expiry(
                        bs_service_id, bs_row_data
                    )
                    dict_step_type_data.update(sms_voice_data)

                else:
                    # Execute Step Type Process = IN PROV SERVICE - UNLI SMS and/or IN PROV SERVICE - UNLI VOICE
                    logger.info("Processing IN PROV SERVICE")
                    sms_voice_data = st.step_type_in_prov_service(
                        double_extend_value, bs_service_id, bs_row_data
                    )
                    dict_step_type_data.update(sms_voice_data)
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
                hlr_ply_data = st.step_type_hlr_ply(bs_service_id, bs_row_data)
                dict_step_type_data.update(hlr_ply_data)
                dict_incharge_extend_data.update(hlr_ply_data)

            else:
                logger.info("Skipping HLR PLY - No creation needed for this Flow")

        except TypeError:
            logger.info(
                "Returned object is empty => hlr_ply_data, proceed to next step.."
            )
            # UPDATE RPA REMARK HERE FOR FAILED CREATION
            pass

        # Add all keys and value to dict_step_type_data dictionary to use later for Flow process
        # logger.info("Merging step data..")
        # dict_step_type_data.update(
        #     {
        #         **in_charge_data,
        #         **extend_first_expiry_data,
        #         **data_volume_bulk_data,
        #         **sms_voice_data,
        #         **hlr_ply_data,
        #     }
        # )

        logger.info(f"Successfully Retreived Step Type Data: {dict_step_type_data}")
        logger.info(f"Old Data: {dict_incharge_extend_data}")

        return dict_step_type_data, dict_incharge_extend_data

    except Exception as e:
        logger.info(f"Something went wrong on prepaid service process\nERROR: {e}")
        raise
