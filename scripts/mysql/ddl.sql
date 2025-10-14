-- MySQL dump 10.13  Distrib 9.4.0, for Linux (x86_64)
--
-- Host: localhost    Database: jobs
-- ------------------------------------------------------
-- Server version	9.4.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `jobs`
--

DROP TABLE IF EXISTS `jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `jobs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `jobId` varchar(100) NOT NULL,
  `title` varchar(300) NOT NULL,
  `company` varchar(200) DEFAULT NULL,
  `location` varchar(200) NOT NULL,
  `url` varchar(300) NOT NULL,
  `markdown` blob NOT NULL,
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `salary` varchar(200) DEFAULT NULL,
  `ignored` tinyint(1) DEFAULT '0',
  `applied` tinyint(1) DEFAULT '0',
  `discarded` tinyint(1) DEFAULT '0',
  `interview_rh` tinyint(1) DEFAULT '0',
  `interview` tinyint(1) DEFAULT '0',
  `interview_tech` tinyint(1) DEFAULT '0',
  `interview_technical_test` tinyint(1) DEFAULT '0',
  `interview_technical_test_done` tinyint(1) DEFAULT '0',
  `comments` blob,
  `ai_enriched` tinyint(1) DEFAULT '0',
  `required_technologies` varchar(1000) DEFAULT NULL,
  `optional_technologies` varchar(1000) DEFAULT NULL,
  `easy_apply` tinyint(1) DEFAULT '0',
  `closed` tinyint(1) DEFAULT '0',
  `seen` tinyint(1) DEFAULT '0',
  `like` tinyint(1) DEFAULT '0',
  `modified` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `client` varchar(200) DEFAULT NULL,
  `flagged` tinyint(1) DEFAULT '0',
  `ai_enrich_error` varchar(500) DEFAULT NULL,
  `web_page` varchar(100) DEFAULT NULL,
  `merged` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `jobId` (`jobId`),
  KEY `title_index` (`title`),
  KEY `company_index` (`company`),
  KEY `client_index` (`client`),
  KEY `salary_index` (`salary`),
  KEY `ignored_index` (`ignored`),
  KEY `seen_index` (`seen`),
  KEY `applied_index` (`applied`),
  KEY `discarded_index` (`discarded`),
  KEY `closed_index` (`closed`)
) ENGINE=InnoDB AUTO_INCREMENT=341286 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-10-10  6:46:51
