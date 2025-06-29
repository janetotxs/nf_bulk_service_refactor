from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.env_loader import get_env_variable
from utils.logger2 import logger
from nf.nf_constants import NfConstants

nf = NfConstants()


def create_message(wd, gs):
    logger.info("STARTING CREATE MESSAGE PROCESS")
    message_fail = False
    message_worksheet = gs.create_worksheet(nf.WORKSHEET_TAB_BULK_SERVICES_TAB_MESSAGES)
    all_rows = message_worksheet.get_all_values()

    for row_index, row_data in enumerate(all_rows[1:], start=2):
        bs_service_id = (
            row_data[nf.NF_MSG_INDEX_SERVICE_ID].strip()
            if len(row_data) > nf.NF_MSG_INDEX_SERVICE_ID
            else ""
        )
        remarks = (
            row_data[nf.NF_MSG_INDEX_REMARKS].strip()
            if len(row_data) > nf.NF_MSG_INDEX_REMARKS
            else ""
        )

        if not bs_service_id or remarks:
            continue

        try:
            message_type = row_data[nf.NF_MSG_INDEX_MESSAGE_TYPE].strip()
            brand = row_data[nf.NF_MSG_INDEX_BRAND].strip()
            channel = row_data[nf.NF_MSG_INDEX_CHANNEL].strip()
            message = row_data[nf.NF_MSG_INDEX_MESSAGE]
            schedule_reminder = row_data[nf.NF_MSG_INDEX_SCHEDULE_REMINDER_HOURS]
            sched_reminder_setting = row_data[nf.NF_MSG_INDEX_SCHEDULE_REMINDER_SETTING]
            category = row_data[nf.NF_MSG_INDEX_CATEGORY]
            notif_type = row_data[nf.NF_MSG_INDEX_TYPE]
            description = row_data[nf.NF_MSG_INDEX_DESCRIPTION]
            subject = row_data[nf.NF_MSG_INDEX_SUBJECT]
            push_channel = row_data[nf.NF_MSG_INDEX_PUSH_NOTIF_CHANNEL]

            logger.info(
                f"Processing row {row_index} for Service ID: {bs_service_id}, Type: {message_type}"
            )

            if message_type == "Reminder Message":

                url_service_msg = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=reminder_messages&op=add&svc_id={bs_service_id}"
                wd.redirect_to_page(url_service_msg, nf.NF_ADD_BTN_INPUT)
                wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

                wd.perform_action(
                    "xpath",
                    f"//select[@name='brand_id']/option[contains(text(), '{brand}')]",
                    "click",
                )
                wd.perform_action("name", "time_diff", "clear")
                wd.perform_action("name", "time_diff", "sendkeys", schedule_reminder)
                wd.perform_action(
                    "xpath",
                    f"//select[@name='reference_event']/option[contains(text(), '{sched_reminder_setting}')]",
                    "click",
                )
                wd.perform_action(
                    "xpath",
                    f"//select[@name='channel']/option[contains(text(), '{channel}')]",
                    "click",
                )

                if channel.lower() == "globe one notification":
                    wd.perform_action("name", "category", "sendkeys", category)
                    wd.perform_action("name", "type", "sendkeys", notif_type)
                    wd.perform_action("name", "description", "sendkeys", description)
                    wd.perform_action("name", "subject", "sendkeys", subject)
                    wd.perform_action(
                        "name", "push_notif_channel", "sendkeys", push_channel
                    )

                wd.perform_action("name", "notif_text", "sendkeys", message)
                logger.info(
                    f"Message has been successfully created for Row: {row_index}"
                )
                # wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
                wd.submit_form_and_wait_for_success(
                    "xpath",
                    nf.NF_ADD_BTN_INPUT,
                    "//div[contains(@class, 'success') or contains(@class, 'error')]",
                    skip=True,
                )
                # gs.update_row(
                #     row_index,
                #     nf.NF_MSG_INDEX_REMARKS + 1,
                #     message_worksheet,
                #     "Success",
                # )

            else:

                url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=service_msgs&op=add&details_id={bs_service_id}"
                wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)
                # wd.wait_until_element("name", "mtype", "visible")
                wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

                wd.perform_action(
                    "xpath",
                    f"//select[@name='mtype']/option[normalize-space(text())='{message_type}']",
                    "click",
                )
                wd.perform_action(
                    "xpath",
                    f"//select[@name='brand_id']/option[contains(text(), '{brand}')]",
                    "click",
                )
                wd.perform_action(
                    "xpath",
                    f"//select[@name='channel']/option[contains(text(), '{channel}')]",
                    "click",
                )

                if channel.lower() == "globe one notification":
                    wd.perform_action("name", "category", "sendkeys", category)
                    wd.perform_action("name", "type", "sendkeys", notif_type)
                    wd.perform_action("name", "description", "sendkeys", description)
                    wd.perform_action("name", "subject", "sendkeys", subject)
                    wd.perform_action(
                        "name", "push_notif_channel", "sendkeys", push_channel
                    )

                wd.perform_action("name", "message", "sendkeys", message)

                logger.info(f"Creating message for Row: {row_index}")
                # wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
                wd.submit_form_and_wait_for_success(
                    "xpath",
                    nf.NF_ADD_BTN_INPUT,
                    "//div[contains(@class, 'success') or contains(@class, 'error')]",
                    skip=True,
                )
            # Update Message RPA Remark
            gs.update_row(
                row_index,
                nf.NF_MSG_INDEX_REMARKS + 1,
                message_worksheet,
                "Success",
            )

            # # Wait for success or error message and update GSheet accordingly
            # try:
            #     WebDriverWait(wd.driver, 10).until(
            #         EC.presence_of_element_located(
            #             (
            #                 By.XPATH,
            #                 "//div[contains(@class, 'success') or contains(@class, 'error')]",
            #             )
            #         )
            #     )
            #     try:
            #         msg = wd.driver.find_element(By.CLASS_NAME, "success").text
            #         # gs.update_row(
            #         #     row_index,
            #         #     nf.NF_MSG_INDEX_REMARKS + 1,
            #         #     message_worksheet,
            #         #     "Success",
            #         # )
            #         # logger.info(f"✅ Row {row_index} success: {msg}")
            #         logger.info("Success Mesage Validated")
            #     except Exception as e:
            #         msg = wd.driver.find_element(By.CLASS_NAME, "error").text
            #         logger.warning(f"❌ Row {row_index} error: {msg}")

            # # modified - 6/24/2025
            # except Exception as wait_e:
            #     wd.driver.execute_script("window.stop();")
            #     msg = wd.driver.find_element(By.CLASS_NAME, "error").text
            #     # fallback = f"⚠️ No success/error message found - {wait_e}"
            #     # logger.warning(f"⚠️ Row {row_index} issue: {fallback}")
            #     logger.info(msg)

        except Exception as inner_e:
            logger.warning("An error has occurred while creaing message, continue..")
            gs.update_row(
                row_index,
                nf.NF_MSG_INDEX_REMARKS + 1,
                message_worksheet,
                "Failed",
            )
            message_fail = True
            continue

    return message_fail
