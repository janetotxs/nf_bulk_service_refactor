class NfConstants:
    GSHEET = "Temp_NF_Bot_Template"
    GSHEET_ID = "14kmKYQh9FG0GHJVMxbdlxoa10Juw0aXCMjp0L1KnNK8"
    WORKSHEET_TAB_CREDENTIAL = "Creds"
    WORKSHEET_TAB_BULK_SERVICES = "BulkService"
    WORKSHEET_TAB_BULK_SERVICES_V2 = "BulkService-V2"
    WORKSHEET_TAB_BULK_SERVICEST_TAB_STEPS = "Steps"
    WORKSHEET_TAB_BULK_SERVICES_TAB_FLOWS = "Flows"
    WORKSHEET_TAB_BULK_SERVICES_TAB_PARAM_MATRIX = "ParamMatrix"
    WORKSHEET_TAB_BULK_SERVICES_TAB_KEYWORDS = "Keywords"
    WORKSHEET_TAB_BULK_SERVICES_TAB_MESSAGES = "Messages"
    WORKSHEET_TAB_BULK_SERVICES_TAB_EXPIRIES = "Expiries"
    WORKSHEET_TAB_BULK_SERVICES_TAB_EXTENSION_EXPIRIES = "ExtensionExpiries"
    WORKSHEET_TAB_BULK_SERVICES_TAB_REMINDER_MESSAGES = "ReminderMessages"
    # NF LOGIN PAGE
    NF_INPUT_USERNAME = "//input[@name='uname']"
    NF_INPUT_PASSWORD = "//input[@name='passwd']"
    NF_LOGIN_BUTTON = "login-button"

    # NF BULK SERVICES > ADD PAGE
    NF_BS_NAME = "//input[@name='name']"
    NF_BS_SERVICE_CLASS_BULK_SERVICE = "//input[@name='service_class' and @value='1']"

    NF_BS_GROUP_STATUS_INQUIRY = "cb_allow_group_status"
    NF_WALLET_TYPE = "//input[@name='wallet_type' and "
    BS_WALLET_TYPE_SMSVOICE = "//input[@name='wallet_type' and @value='1']"
    BS_WALLET_TYPE_DATA = "//input[@name='wallet_type' and @value='29']"
    BS_WALLET_TYPE_SPS = "//input[@name='wallet_type' and @value='52']"
    BS_WALLET_TYPE_CPS = "//input[@name='wallet_type' and @value='3']"

    NF_BS_STATUS = "//select[@name='status']"
    BS_STATUS_ACTIVE = "//select[@name='status']//option[@value='1']"
    BS_STATUS_NOPROV = "//select[@name='status']//option[@value='2']"
    BS_STATUS_INACTIVE = "//select[@name='status']//option[@value='3']"

    # hardcode
    NF_BS_PRIORITY = "//select[@name='priority']//option[@value='1']"
    NF_BS_THREAD_COUNT_INPUT_NAME = "thread_count"
    NF_BS_TYPE_TIME_BASED = "//select[@name='btype']//option[@value='1']"
    NF_BS_TYPE_WALLET_BASED = "//select[@name='btype']//option[@value='2']"

    # brands-v1
    NF_BS_BRAND_GHP = "brand1"
    NF_BS_BRAND_TM = "brand2"
    NF_BS_BRAND_POSTPAID = "brand3"
    NF_BS_BRAND_DEEDSFOREIGN = "brand4"
    NF_BS_BRAND_DEEPLO = "brand5"
    NF_BS_BRAND_PW = "brand6"
    NF_BS_BRAND_PWN = "brand7"
    NF_BS_BRAND_TESTINGRBA = "brand8"
    # brands-v2

    # name #hardcode
    NF_BS_TIMEOUT_SEC = "timeout_seconds"

    # name
    NF_BS_SMP_NAME = "smp_name"

    # name
    NF_BS_DEFAULT_ACCESS_CODE = "access_code"

    # name #hardcode
    NF_BS_QUEUE_LIMIT = "queue_limit"
    NF_BS_DEPROV_ON_EMPTY_YES = "//input[@id='deprov_on_empty' and @value='1']"
    NF_BS_DEPROV_ON_EMPTY_NO = "//input[@id='notdeprov_on_empty' and @value='0']"

    # hardcode
    NF_BS_CANCEL_PRE_EXPIRY_YES = "//input[@id='cancel_preex_on_empty' and @value='1']"
    NF_BS_CANCEL_PRE_EXPIRY_NO = (
        "//input[@id='notcancel_preex_on_empty' and @value='0']"
    )

    # id
    NF_BS_SUBSCRIPTION_LESS = "subscriptionless"
    NF_BS_NOTSUBSCRIPTION_LESS = "notsubscriptionless"

    # hardcode #id
    NF_BS_MAX_RECURRENCE = "no_recurrence_limit"
    NF_MAX_NO_RECURRNECE = "no_recurrence"
    # name
    NF_MAX_RECURRENCE_VALUE = "max_recurrence_value"

    # name
    NF_BS_MAX_DAILY_EXTENSION = "max_daily_extensions"
    # name
    NF_BS_MAX_TOTAL_EXTENSION = "max_total_extensions"

    # name
    NF_BS_PROMO_NAME = "promo_name"

    # name
    NF_BS_COMM_POOL_YES = "//input[@name='is_comm_pool' and @value='1']"
    NF_BS_COMM_POOL_NO = "//input[@name='is_comm_pool' and @value='0']"

    NF_ADD_BTN_INPUT = "//input[@type='submit']"

    # DATA SERVICES > ADD PAGE
    NF_DATA_SERVICES_TITLE = "//div[@id='title']"
    NF_DATA_SERVICES_INPUT_NAME = "name"
    NF_DATA_SERVICE_TYPE_WALLET_BASED = "//select[@name='stype']//option[@value='2']"
    NF_DATA_SERVICES_COMMERCIAL_WALLET_NAME_INPUT = "commercial_wallet_name"
    NF_DATA_SERVICES_ADD_BUTTON_NAME = "submit"

    # SERVICES STEPS > ADD PAGE
    NF_STEPS_NAME_INPUT = "name"
    NF_STEPS_FINAL_CHECKBOX = "final"
    NF_STEPS_RETRY_INPUT = "retry"

    # SERVICES FLOW > ADD PAGE
    NF_FLOWS_NAME_INPUT = "name"

    # SERVICES KEYWORDS > ADD PAGE
    NF_KEYWORDS_BULK_SERVICES_DROPDOWN = "svc_id"
    NF_KEYWORDS_REGEX_INPUT_NAME = "regex"
    NF_KEYWORDS_REPLY = "//input[@name='reply']"
    NF_KEYWORDS_REPLY_DISABLED = "//input[@name='reply' and @disabled]"


class SMPConstants:
    GSHEET = "SMP_RolloutDeploymentRecords"
    GSHEET_ID = "1oOQvejlcZkVY5nfK4fh5QYZoTYrFM6wvhga2e411nyk"
    WORKSHEET_TAB_CREDENTIAL = "Creds"
