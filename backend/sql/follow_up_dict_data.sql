-- Follow-up Dictionary Data (跟进方式、跟进结论)

-- 跟进方式 (Follow-up Methods)
INSERT INTO dict_items (dict_type, code, name, sort_order, is_active) VALUES
('跟进方式', 'phone', '电话沟通', 1, true),
('跟进方式', 'wechat', '微信沟通', 2, true),
('跟进方式', 'email', '邮件沟通', 3, true),
('跟进方式', 'visit', '上门拜访', 4, true),
('跟进方式', 'meeting', '会议交流', 5, true),
('跟进方式', 'demo', '产品演示', 6, true),
('跟进方式', 'proposal', '方案报价', 7, true),
('跟进方式', 'contract', '合同洽谈', 8, true),
('跟进方式', 'other', '其他方式', 9, true);

-- 跟进结论 (Follow-up Conclusions)
INSERT INTO dict_items (dict_type, code, name, sort_order, is_active) VALUES
('跟进结论', 'positive', '有意向', 1, true),
('跟进结论', 'pending', '待进一步沟通', 2, true),
('跟进结论', 'negotiating', '商务谈判中', 3, true),
('跟进结论', 'quoted', '已报价待反馈', 4, true),
('跟进结论', 'confirmed', '已确认需求', 5, true),
('跟进结论', 'signed', '已签约', 6, true),
('跟进结论', 'rejected', '暂无意向', 7, true),
('跟进结论', 'lost', '已流失', 8, true),
('跟进结论', 'follow_up', '需持续跟进', 9, true);