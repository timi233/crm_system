-- 1. 地区字典
INSERT INTO dict_items (id, dict_type, code, name, parent_id, sort_order, is_active) VALUES
(1, '地区', '37', '山东省', NULL, 1, true),
(101, '地区', '3701', '济南市', 1, 1, true),
(102, '地区', '3702', '青岛市', 1, 2, true),
(103, '地区', '3703', '淄博市', 1, 3, true),
(104, '地区', '3704', '枣庄市', 1, 4, true),
(105, '地区', '3705', '东营市', 1, 5, true),
(106, '地区', '3706', '烟台市', 1, 6, true),
(107, '地区', '3707', '潍坊市', 1, 7, true),
(108, '地区', '3708', '济宁市', 1, 8, true),
(109, '地区', '3709', '泰安市', 1, 9, true),
(110, '地区', '3710', '威海市', 1, 10, true),
(111, '地区', '3711', '日照市', 1, 11, true),
(112, '地区', '3713', '临沂市', 1, 12, true),
(113, '地区', '3714', '德州市', 1, 13, true),
(114, '地区', '3715', '聊城市', 1, 14, true),
(115, '地区', '3716', '滨州市', 1, 15, true),
(116, '地区', '3717', '菏泽市', 1, 16, true);

-- 2. 行业字典
INSERT INTO dict_items (id, dict_type, code, name, parent_id, sort_order, is_active) VALUES
(2, '行业', 'GOV', '政府单位', NULL, 1, true),
(3, '行业', 'PSU', '事业单位', NULL, 2, true),
(4, '行业', 'OTHER', '其他', NULL, 3, true),
(5, '行业', 'MFG', '制造', NULL, 4, true),
(6, '行业', 'CHEM', '化工', NULL, 5, true),
(7, '行业', 'PHA', '医药', NULL, 6, true),
(8, '行业', 'ENER', '能源', NULL, 7, true),
(9, '行业', 'AUTO', '汽车', NULL, 8, true),
(10, '行业', 'CHIP', '芯片', NULL, 9, true),
(11, '行业', 'IT', '信息技术', NULL, 10, true),
(12, '行业', 'FIN', '金融', NULL, 11, true),
(13, '行业', 'EDU', '教育', NULL, 12, true),
(14, '行业', 'HEALTH', '医疗', NULL, 13, true),
(15, '行业', 'RETAIL', '零售', NULL, 14, true),
(16, '行业', 'LOGST', '物流', NULL, 15, true),
(17, '行业', 'CONST', '建筑', NULL, 16, true),
(18, '行业', 'AGRI', '农业', NULL, 17, true),
(19, '行业', 'TELECOM', '通信', NULL, 18, true),
(20, '行业', 'MEDIA', '传媒', NULL, 19, true);

-- 3. 商机来源字典
INSERT INTO dict_items (id, dict_type, code, name, parent_id, sort_order, is_active) VALUES
(21, '商机来源', 'REF', '客户推荐', NULL, 1, true),
(22, '商机来源', 'WEB', '网络推广', NULL, 2, true),
(23, '商机来源', 'EXPO', '展会', NULL, 3, true),
(24, '商机来源', 'CALL', '电话营销', NULL, 4, true),
(25, '商机来源', 'EXIST', '老客户二次开发', NULL, 5, true),
(26, '商机来源', 'PART', '合作伙伴推荐', NULL, 6, true);

-- 4. 客户状态字典
INSERT INTO dict_items (id, dict_type, code, name, parent_id, sort_order, is_active) VALUES
(27, '客户状态', 'POTENTIAL', '潜在', NULL, 1, true),
(28, '客户状态', 'ACTIVE', '活跃', NULL, 2, true),
(29, '客户状态', 'CONTRACTED', '已签约', NULL, 3, true),
(30, '客户状态', 'DORMANT', '休眠', NULL, 4, true),
(31, '客户状态', 'CHURNED', '流失', NULL, 5, true);

-- 5. 跟进方式字典
INSERT INTO dict_items (id, dict_type, code, name, parent_id, sort_order, is_active) VALUES
(32, '跟进方式', 'phone', '电话沟通', NULL, 1, true),
(33, '跟进方式', 'wechat', '微信沟通', NULL, 2, true),
(34, '跟进方式', 'email', '邮件沟通', NULL, 3, true),
(35, '跟进方式', 'visit', '上门拜访', NULL, 4, true),
(36, '跟进方式', 'meeting', '会议交流', NULL, 5, true),
(37, '跟进方式', 'demo', '产品演示', NULL, 6, true),
(38, '跟进方式', 'proposal', '方案报价', NULL, 7, true),
(39, '跟进方式', 'contract', '合同洽谈', NULL, 8, true),
(40, '跟进方式', 'other', '其他方式', NULL, 9, true);

-- 6. 跟进结论字典
INSERT INTO dict_items (id, dict_type, code, name, parent_id, sort_order, is_active) VALUES
(41, '跟进结论', 'positive', '有意向', NULL, 1, true),
(42, '跟进结论', 'pending', '待进一步沟通', NULL, 2, true),
(43, '跟进结论', 'negotiating', '商务谈判中', NULL, 3, true),
(44, '跟进结论', 'quoted', '已报价待反馈', NULL, 4, true),
(45, '跟进结论', 'confirmed', '已确认需求', NULL, 5, true),
(46, '跟进结论', 'signed', '已签约', NULL, 6, true),
(47, '跟进结论', 'rejected', '暂无意向', NULL, 7, true),
(48, '跟进结论', 'lost', '已流失', NULL, 8, true),
(49, '跟进结论', 'follow_up', '需持续跟进', NULL, 9, true);

-- 7. 产品类型字典
INSERT INTO dict_items (id, dict_type, code, name, parent_id, sort_order, is_active) VALUES
(50, 'product_type', 'server', '服务器', NULL, 1, true),
(51, 'product_type', 'storage', '存储设备', NULL, 2, true),
(52, 'product_type', 'network', '网络设备', NULL, 3, true),
(53, 'product_type', 'software', '软件系统', NULL, 4, true),
(54, 'product_type', 'security', '安全设备', NULL, 5, true);

-- 8. 品牌字典 (parent_id关联产品类型)
INSERT INTO dict_items (id, dict_type, code, name, parent_id, sort_order, is_active) VALUES
(55, 'brand', 'dell', 'Dell', 50, 1, true),
(56, 'brand', 'hp', 'HP', 50, 2, true),
(57, 'brand', 'lenovo', '联想', 50, 3, true),
(58, 'brand', 'huawei', '华为', 50, 4, true),
(59, 'brand', 'netapp', 'NetApp', 51, 1, true),
(60, 'brand', 'dellemc', 'Dell EMC', 51, 2, true);

-- 9. 型号字典 (parent_id关联品牌)
INSERT INTO dict_items (id, dict_type, code, name, parent_id, sort_order, is_active) VALUES
(61, 'model', 'dell_r740', 'Dell PowerEdge R740', 55, 1, true),
(62, 'model', 'dell_r750', 'Dell PowerEdge R750', 55, 2, true),
(63, 'model', 'dell_r940', 'Dell PowerEdge R940', 55, 3, true),
(64, 'model', 'hp_dl380', 'HP ProLiant DL380', 56, 1, true),
(65, 'model', 'hp_dl360', 'HP ProLiant DL360', 56, 2, true),
(66, 'model', 'netapp_fas', 'NetApp FAS系列', 59, 1, true),
(67, 'model', 'dellemc_powervault', 'Dell EMC PowerVault', 60, 1, true);

-- 修复序列
SELECT setval('dict_items_id_seq', (SELECT MAX(id) FROM dict_items));