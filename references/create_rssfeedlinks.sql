# Create rssfeed_links table for articles database
# http://dev.mysql.com/doc/refman/5.7/en/create-table.html

DROP TABLE IF EXISTS rssfeed_links;
#@ _CREATE_TABLE_
CREATE TABLE rssfeed_links
(
	id			INT NOT NULL AUTO_INCREMENT,
	title		VARCHAR(300) NOT NULL,
	link		VARCHAR(300) NOT NULL,
	published	DATETIME NOT NULL,
	summary		VARCHAR(5000),
	story_id	VARCHAR(50),
	rss_link	VARCHAR(100) NOT NULL,
	PRIMARY KEY (id),
) ENGINE = InnoDB;
#@ _CREATE_TABLE_
