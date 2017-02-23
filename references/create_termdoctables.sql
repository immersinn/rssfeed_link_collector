# Create rssfeed_links table for articles database
# http://dev.mysql.com/doc/refman/5.7/en/create-table.html

DROP TABLE IF EXISTS words;
#@ _CREATE_TABLE_
CREATE TABLE words
(
	id			INT NOT NULL AUTO_INCREMENT,
	word		VARCHAR(200) NOT NULL,
	PRIMARY KEY (id)
) ENGINE = InnoDB;
#@ _CREATE_TABLE_


DROP TABLE IF EXISTS doc_bows;
#@ _CREATE_TABLE_
CREATE TABLE doc_bows
(
	word_id		INT NOT NULL,
	doc_id		INT NOT NULL,
	wcount		INT NOT NULL,
	PRIMARY KEY (word_id, doc_id),
	FOREIGN KEY (word_id) REFERENCES words (id),
	FOREIGN KEY (doc_id) REFERENCES rssfeed_links (id)
) ENGINE = InnoDB;
#@ _CREATE_TABLE_
