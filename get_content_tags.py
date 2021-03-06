__author__ = 'Desmond'

import jieba
import jieba.analyse
import jieba.posseg
import mysql.connector
from mysql.connector import errorcode

from weibo_predict_data import WeiboPredictData
from weibo_train_data import WeiboTrainData
from sql_config import *


def get_train_data_features(cur, WeiboData):
    with WeiboData() as weibo_data:

        k = 30
        is_with_weight = True
        pos = ('n', 'r', 'nr', 'ns', 'vn', 'v')

        cnt = 0
        cnt_up = 0
        DEBUG = False
        query = weibo_data.get_all()
        for line in query:
            cnt += 1
            if cnt >= cnt_up:
                print(cnt)
                cnt_up += 1000

            if DEBUG:
                if cnt < 0:
                    continue
                if cnt > 20:
                    break

            # cur.execute("SELECT DISTINCT mid FROM features_tags WHERE mid = `{}`".format(line[1]))
            # if cur.fetchall().count() > 0:
            #     continue

            # type1
            tags_idf = jieba.analyse.extract_tags(line[-1], topK=k, withWeight=is_with_weight,
                                                  allowPOS=pos)
            # type2
            tags_text_rank = jieba.analyse.textrank(line[-1], topK=k, withWeight=is_with_weight,
                                                    allowPOS=pos)

            tags_dict = {}
            for tag in tags_idf:
                tags_dict[tag[0]] = [tag[1], 0]
            for tag in tags_text_rank:
                if tag[0] in tags_dict:
                    tags_dict[tag[0]][1] = tag[1]
                else:
                    tags_dict[tag[0]] = [0, tag[1]]
            for tag, val in tags_dict.iteritems():
                try:
                    cur.execute(add_ddl, (line[1], line[2], tag, val[0], val[1]))
                except mysql.connector.Error as err0:
                    print(err0.msg)
                    print(tag)
                    break

            if DEBUG:
                print(line[-1])
                if is_with_weight is True:
                    for tag in tags_idf:
                        print("%s\t%f" % (tag[0], tag[1]))
                    print '-----'
                    for tag in tags_text_rank:
                        print("%s\t%f" % (tag[0], tag[1]))
                else:
                    print(", ".join(tags_idf))
                    print(", ".join(tags_text_rank))
                print


try:
    cnx = mysql.connector.connect(**DB_CONFIG)
    cnx.database = DB_NAME
    cursor = cnx.cursor()

    cursor.execute("DROP TABLE IF EXISTS `features_tags`")
    cursor.execute("CREATE TABLE IF NOT EXISTS `features_tags` ("
                   "`mid` char(32) NOT NULL,"
                   "`time` date NOT NULL,"
                   "`tag` varchar(32) NOT NULL,"
                   "`confidence1` float NOT NULL,"
                   "`confidence2` float NOT NULL"
                   ") ENGINE=MyISAM DEFAULT CHARSET=utf8mb4;")
    cursor.execute("ALTER TABLE `features_tags` ADD INDEX(`mid`);")
    cursor.execute("ALTER TABLE `features_tags` ADD INDEX(`time`);")
    cursor.execute("ALTER TABLE `features_tags` ADD INDEX(`tag`);")

    add_ddl = ("INSERT INTO `features_tags` "
               "(mid, time, tag, confidence1, confidence2) "
               "VALUES (%s, %s, %s, %s, %s)")

    get_train_data_features(cursor, WeiboTrainData)  # 15314770
    get_train_data_features(cursor, WeiboPredictData)

    cursor.close()
    cnx.close()
except mysql.connector.Error as err:
    print(err.msg)
