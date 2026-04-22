import React, { useState, useEffect } from 'react';
import { Badge } from 'antd';
import { CheckCircleOutlined, TrophyOutlined, FundProjectionScreenOutlined, UsergroupAddOutlined } from '@ant-design/icons';
import './AchievementBadge.css';

interface AchievementBadgeProps {
  achievement: {
    id: string;
    name: string;
    icon: 'trophy' | 'fund' | 'user' | 'custom';
    description?: string;
    targetValue?: number;
    currentValue?: number;
  };
  unlocked: boolean;
}

const AchievementBadge: React.FC<AchievementBadgeProps> = ({ achievement, unlocked }) => {
  const [showCelebration, setShowCelebration] = useState(false);

  useEffect(() => {
    if (unlocked) {
      setShowCelebration(true);
      const timer = setTimeout(() => setShowCelebration(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [unlocked]);

  const getIcon = (iconType: string) => {
    switch (iconType) {
      case 'trophy':
        return <TrophyOutlined />;
      case 'fund':
        return <FundProjectionScreenOutlined />;
      case 'user':
        return <UsergroupAddOutlined />;
      default:
        return <TrophyOutlined />;
    }
  };

  const progress = achievement.targetValue && achievement.currentValue 
    ? Math.min(100, (achievement.currentValue / achievement.targetValue) * 100)
    : 0;

  return (
    <div className="achievement-badge">
      {showCelebration && (
        <div className="celebration-animation">
          <div className="confetti confetti-1"></div>
          <div className="confetti confetti-2"></div>
          <div className="confetti confetti-3"></div>
        </div>
      )}
      
      <Badge.Ribbon 
        text={unlocked ? "已解锁" : "进行中"} 
        color={unlocked ? "#10B981" : "#667eea"}
        className="achievement-ribbon"
      >
        <div className={`achievement-card ${unlocked ? 'unlocked' : ''}`}>
          <div className="achievement-icon">
            {getIcon(achievement.icon)}
          </div>
          <div className="achievement-content">
            <h4 className="achievement-title">{achievement.name}</h4>
            {achievement.description && (
              <p className="achievement-description">{achievement.description}</p>
            )}
            {!unlocked && achievement.targetValue && (
              <div className="achievement-progress">
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                <span className="progress-text">
                  {achievement.currentValue || 0} / {achievement.targetValue}
                </span>
              </div>
            )}
          </div>
          {unlocked && <CheckCircleOutlined className="check-icon" />}
        </div>
      </Badge.Ribbon>
    </div>
  );
};

export default AchievementBadge;