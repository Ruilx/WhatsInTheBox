-- =============================================================
-- 「箱子里面有什么（WhatsInTheBox）」数据库初始化脚本
-- 字符集：utf8mb4 + utf8mb4_general_ci
-- 时区：连接会话统一 Asia/Shanghai（由后端连接时设置）
-- 逻辑删除：每表 deleted unsigned tinyint（0 未删 / 1 已删）
-- 枚举：status / join_method 等用 unsigned tinyint + 列 COMMENT 写清映射
-- 唯一性：采用应用层校验（不建含 deleted 的唯一索引），软删后可重用
-- 注意：box_id = 0 为「已取出/没放箱里」哨兵，非真实箱
-- =============================================================

CREATE DATABASE IF NOT EXISTS `whatsinthebox`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_general_ci;

USE `whatsinthebox`;

-- 通用字段约定：
--   deleted      TINYINT UNSIGNED NOT NULL DEFAULT 0  逻辑删除
--   create_time  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
--   update_time  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

-- -------------------- user 用户表 --------------------
CREATE TABLE IF NOT EXISTS `whatsinthebox`.`user` (
    `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `username`      VARCHAR(64)  NOT NULL                COMMENT '登录名（全局唯一，应用层校验）',
    `password_hash` VARCHAR(128) NOT NULL                COMMENT 'sha256(salt+password)',
    `salt`          VARCHAR(64)  NOT NULL                COMMENT '每用户随机盐',
    `nickname`      VARCHAR(64)  NOT NULL DEFAULT ''     COMMENT '昵称',
    `role`          VARCHAR(8)   NOT NULL DEFAULT 'rw'   COMMENT 'rw 读写 / ro 只读',
    `deleted`       TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `create_time`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_user_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='用户表';

-- -------------------- session 会话表（物理删除，无 deleted） --------------------
CREATE TABLE IF NOT EXISTS `whatsinthebox`.`session` (
    `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id`     BIGINT UNSIGNED NOT NULL               COMMENT '关联 user.id',
    `token`       VARCHAR(128) NOT NULL                  COMMENT '随机 token，仅存于 cookie',
    `ip`          VARCHAR(64)  NOT NULL DEFAULT ''       COMMENT '来源 IP',
    `user_agent`  VARCHAR(512) NOT NULL DEFAULT ''       COMMENT '浏览器 UA',
    `expire_at`   DATETIME     NOT NULL                  COMMENT '过期时间（4h + 滑动续期）',
    `create_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_session_token` (`token`),
    KEY `idx_session_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='会话表（多端登录，无 Redis）';

-- -------------------- activity 活动表 --------------------
CREATE TABLE IF NOT EXISTS `whatsinthebox`.`activity` (
    `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name`        VARCHAR(128) NOT NULL                  COMMENT '活动名（全局唯一 URL 前缀，禁止等于系统保留前缀）',
    `desc`        VARCHAR(512) NOT NULL DEFAULT ''       COMMENT '活动描述',
    `type`        VARCHAR(64)  NOT NULL DEFAULT ''       COMMENT '活动类型（自由文本）',
    `start_time`  DATETIME     DEFAULT NULL              COMMENT '活动开始时间',
    `end_time`    DATETIME     DEFAULT NULL              COMMENT '活动结束时间',
    `status`      TINYINT UNSIGNED NOT NULL DEFAULT 0    COMMENT '0 draft 草稿 / 1 active 进行中 / 2 stopped 已停止 / 3 archived 归档',
    `note`        VARCHAR(512) NOT NULL DEFAULT ''       COMMENT '备注（活动要求等）',
    `deleted`     TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `create_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_activity_name` (`name`),
    KEY `idx_activity_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='活动表';

-- -------------------- box 箱子表 --------------------
CREATE TABLE IF NOT EXISTS `whatsinthebox`.`box` (
    `id`               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `activity_id`      BIGINT UNSIGNED NOT NULL           COMMENT '关联 activity.id',
    `name`             VARCHAR(128) NOT NULL              COMMENT '箱子编号/名称（活动内唯一，即 URL 路径段）',
    `desc`             VARCHAR(512) NOT NULL DEFAULT ''   COMMENT '箱子描述',
    `type`             JSON         DEFAULT NULL          COMMENT '多标签数组：主要/次要/易碎/需保护/防水/要求向上/旧箱',
    `size`             VARCHAR(64)  NOT NULL DEFAULT ''   COMMENT '箱子大小',
    `material`         VARCHAR(64)  NOT NULL DEFAULT ''   COMMENT '箱子材质',
    `parent_box_id`    BIGINT UNSIGNED DEFAULT NULL       COMMENT '父箱 id（自引用，多层嵌套；NULL 为顶层）',
    `status`           TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0 open 打开 / 1 folded 折叠 / 2 sealed 封存 / 3 in_transit 运输中 / 4 damaged 损伤 / 5 retired 淘汰',
    `serial_no`        VARCHAR(128) NOT NULL DEFAULT ''   COMMENT '物理箱子唯一串号（全局唯一、不可变、软删清空）',
    `photo`            VARCHAR(512) NOT NULL DEFAULT ''   COMMENT '照片相对路径',
    `thumb`            VARCHAR(512) NOT NULL DEFAULT ''   COMMENT '缩略图相对路径',
    `note`             VARCHAR(512) NOT NULL DEFAULT ''   COMMENT '备注（防摔、防水等）',
    `first_using_time` DATETIME     DEFAULT NULL          COMMENT '第一次使用时间',
    `deleted`          TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `create_time`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_box_activity_name` (`activity_id`, `name`),
    KEY `idx_box_activity` (`activity_id`),
    KEY `idx_box_parent` (`parent_box_id`),
    KEY `idx_box_serial` (`serial_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='箱子表';

-- -------------------- item 物品表 --------------------
CREATE TABLE IF NOT EXISTS `whatsinthebox`.`item` (
    `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name`        VARCHAR(128) NOT NULL                  COMMENT '物品名称',
    `desc`        VARCHAR(512) NOT NULL DEFAULT ''       COMMENT '物品描述',
    `type`        VARCHAR(64)  NOT NULL DEFAULT ''       COMMENT '物品类型（自由文本）',
    `activity_id` BIGINT UNSIGNED NOT NULL DEFAULT 0    COMMENT '冗余列：所属活动 id（取出 box_id=0 时仍需此列定位活动）',
    `box_id`      BIGINT UNSIGNED NOT NULL DEFAULT 0    COMMENT '当前所在箱；0 = 已取出/没放箱里哨兵（非真实箱）',
    `photo`       VARCHAR(512) NOT NULL DEFAULT ''       COMMENT '照片相对路径',
    `thumb`       VARCHAR(512) NOT NULL DEFAULT ''       COMMENT '缩略图相对路径',
    `status`      TINYINT UNSIGNED NOT NULL DEFAULT 0    COMMENT '0 in_box 在箱 / 1 taken_out 已取出 / 2 lent 借出 / 3 damaged 损坏 / 4 lost 遗失',
    `note`        VARCHAR(512) NOT NULL DEFAULT ''       COMMENT '备注',
    `deleted`     TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `create_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_item_activity` (`activity_id`),
    KEY `idx_item_box` (`box_id`),
    KEY `idx_item_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='物品表';

-- -------------------- combo 联合物品表 --------------------
CREATE TABLE IF NOT EXISTS `whatsinthebox`.`combo` (
    `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name`        VARCHAR(128) NOT NULL                  COMMENT '联合物品名称',
    `type`        VARCHAR(64)  NOT NULL DEFAULT ''       COMMENT '联合物品类型',
    `status`      TINYINT UNSIGNED NOT NULL DEFAULT 0    COMMENT '0 normal 正常 / 1 invalid 失效',
    `note`        VARCHAR(512) NOT NULL DEFAULT ''       COMMENT '备注（后配、注意事项）',
    `deleted`     TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `create_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_combo_name` (`name`),
    KEY `idx_combo_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='联合物品表';

-- -------------------- combo_item 联合物品成员表 --------------------
CREATE TABLE IF NOT EXISTS `whatsinthebox`.`combo_item` (
    `id`           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `combo_id`     BIGINT UNSIGNED NOT NULL              COMMENT '关联 combo.id',
    `item_id`      BIGINT UNSIGNED NOT NULL              COMMENT '关联 item.id',
    `item_status`  VARCHAR(32)  NOT NULL DEFAULT ''      COMMENT '成员状态（原装/补配等自由文本快照）',
    `join_method`  TINYINT UNSIGNED NOT NULL DEFAULT 0   COMMENT '0 original 原装 / 1 supplement 补配 / 2 replaced 已替代',
    `deleted`      TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `create_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_comboitem_combo` (`combo_id`),
    KEY `idx_comboitem_item` (`item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='联合物品成员表';

-- -------------------- log 日志表（实质只追加） --------------------
CREATE TABLE IF NOT EXISTS `whatsinthebox`.`log` (
    `id`           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `activity_id`  BIGINT UNSIGNED DEFAULT NULL          COMMENT '关联活动（可空）',
    `box_id`       BIGINT UNSIGNED DEFAULT NULL          COMMENT '关联箱子（可空）',
    `item_id`      BIGINT UNSIGNED DEFAULT NULL          COMMENT '关联物品（可空）',
    `combo_id`     BIGINT UNSIGNED DEFAULT NULL          COMMENT '关联联合物品（可空）',
    `user_id`      BIGINT UNSIGNED NOT NULL DEFAULT 0    COMMENT '操作人（当前 session 用户）',
    `action`       VARCHAR(32)  NOT NULL                 COMMENT 'query/view/create/update/delete/take_out/place/login/logout/scan（全量记录，含读操作）',
    `object_type`  VARCHAR(16)  NOT NULL DEFAULT ''      COMMENT 'activity/box/item/combo',
    `object_id`    BIGINT UNSIGNED NOT NULL DEFAULT 0    COMMENT '对象 id',
    `detail`       VARCHAR(1024) NOT NULL DEFAULT ''     COMMENT '变更前后值 / 备注',
    `ip`           VARCHAR(64)  DEFAULT NULL             COMMENT '来源 IP（可空）',
    `deleted`      TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `create_time`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_log_action` (`action`),
    KEY `idx_log_object` (`object_type`, `object_id`),
    KEY `idx_log_user` (`user_id`),
    KEY `idx_log_create` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='操作日志表（全量记录，含读操作）';
