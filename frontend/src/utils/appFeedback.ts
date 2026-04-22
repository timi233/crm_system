import type { MessageInstance } from 'antd/es/message/interface';
import type { HookAPI as ModalHookApi } from 'antd/es/modal/useModal';

let messageApi: MessageInstance | null = null;
let modalApi: ModalHookApi | null = null;

export const registerAppFeedback = (
  message: MessageInstance,
  modal: ModalHookApi
) => {
  messageApi = message;
  modalApi = modal;
};

export const appMessage = {
  success(content: string) {
    messageApi?.success(content);
  },
  error(content: string) {
    messageApi?.error(content);
  },
  warning(content: string) {
    messageApi?.warning(content);
  },
  info(content: string) {
    messageApi?.info(content);
  },
};

export const appModal = {
  confirm: (...args: Parameters<ModalHookApi['confirm']>) => modalApi?.confirm(...args),
  warning: (...args: Parameters<ModalHookApi['warning']>) => modalApi?.warning(...args),
  error: (...args: Parameters<ModalHookApi['error']>) => modalApi?.error(...args),
  info: (...args: Parameters<ModalHookApi['info']>) => modalApi?.info(...args),
  success: (...args: Parameters<ModalHookApi['success']>) => modalApi?.success(...args),
};
