import { App } from 'antd';
import { useEffect } from 'react';

import { registerAppFeedback } from '../../utils/appFeedback';

const AppFeedbackBridge: React.FC = () => {
  const { message, modal } = App.useApp();

  useEffect(() => {
    registerAppFeedback(message, modal);
  }, [message, modal]);

  return null;
};

export default AppFeedbackBridge;
