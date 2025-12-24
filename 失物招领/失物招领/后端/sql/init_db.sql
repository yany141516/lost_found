CREATE TABLE `user` (
  `user_id` INT PRIMARY KEY AUTO_INCREMENT,
  `username` VARCHAR(20) NOT NULL UNIQUE,
  `password` VARCHAR(255) NOT NULL,
  `contact` VARCHAR(100) NOT NULL UNIQUE,
  `is_admin` TINYINT(1) NOT NULL DEFAULT 0
);

CREATE TABLE `lost_item` (
  `item_id` INT PRIMARY KEY AUTO_INCREMENT,
  `item_name` VARCHAR(100) NOT NULL,
  `category` ENUM('证件','电子设备','衣物','书籍','其他') NOT NULL,
  `description` TEXT,
  `location` VARCHAR(100) NOT NULL,
  `event_time` DATETIME NOT NULL,
  `item_type` ENUM('丢失','拾获') NOT NULL,
  `image_path` VARCHAR(255),
  `status` ENUM('待审核','已发布','已认领','已驳回') NOT NULL DEFAULT '待审核',
  `publish_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `user_id` INT NOT NULL,
  FOREIGN KEY (`user_id`) REFERENCES `user`(`user_id`)
);

CREATE TABLE `audit_record` (
  `audit_id` INT PRIMARY KEY AUTO_INCREMENT,
  `item_id` INT NOT NULL,
  `admin_id` INT NOT NULL,
  `result` ENUM('通过','驳回') NOT NULL,
  `reason` VARCHAR(255),
  `audit_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`item_id`) REFERENCES `lost_item`(`item_id`) ON DELETE CASCADE,
  FOREIGN KEY (`admin_id`) REFERENCES `user`(`user_id`)
);

CREATE TABLE `comment` (
  `comment_id` INT PRIMARY KEY AUTO_INCREMENT,
  `item_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `content` VARCHAR(200) NOT NULL,
  `comment_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`item_id`) REFERENCES `lost_item`(`item_id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `user`(`user_id`) ON DELETE CASCADE
);
