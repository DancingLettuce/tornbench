
#id,name,gender,signed_up,level,rank,donator,faction,company,job,spouse,display_case,bazaar,fed,fed_reason,time_played,awards
/*id,name,gender,signed_up,level,rank,donator,faction,company,job,spouse,display_case,bazaar,fed,fed_reason,time_played,awards
        1,Chedburn,Male,1100521336,15,Outstanding,1,40992,79286,,2103253,1,1,0,,48596767,1411
        5,Tebbs,Male,1100521055,95,Elite,1,46166,114356,,253773,1,0,0,,4381288,394
        12,SandyClaws,Male,1100522080,36,Outstanding,1,9745,77427,,97534,1,1,0,,2056518,344"""*/
drop table if exists tb_player_snapshot_staging;
/*
CREATE TABLE if not exists tb_player_snapshot_staging (
  id bigint NOT NULL AUTO_INCREMENT,
  created_on datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  updated_on datetime(6) DEFAULT NULL,
  chit varchar(250) NOT NULL DEFAULT '',
  player_id  varchar(200) DEFAULT NULL,
  name  varchar(200) DEFAULT NULL,
  gender varchar(200) DEFAULT NULL,
  signed_up varchar(200) DEFAULT NULL,
  level  varchar(200) DEFAULT NULL,
  player_rank varchar(200) DEFAULT NULL,
  donator varchar(200) DEFAULT NULL,
  faction  varchar(200) DEFAULT NULL,
  company  varchar(200) DEFAULT NULL,
  job  varchar(200) DEFAULT NULL,
  spouse  varchar(200) DEFAULT NULL,
  display_case  varchar(200) DEFAULT NULL,
  bazaar  varchar(200) DEFAULT NULL,
  fed  varchar(200) DEFAULT NULL,
  fed_reason  varchar(200) DEFAULT NULL,
  time_played  varchar(200) DEFAULT NULL,
  awards  varchar(200) DEFAULT NULL,
  update_on_viasnapshotapi datetime(6) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY tb_player_snapshot_staging_player_id (player_id)
) ;
*/


CREATE TABLE if not exists tb_player_snapshot_staging (
  id bigint NOT NULL AUTO_INCREMENT,
  created_on datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  updated_on datetime(6) DEFAULT NULL,
  chit varchar(250) NOT NULL DEFAULT '',
  player_id  bigint NOT NULL,
  name  varchar(200) DEFAULT '' NULL,
  gender varchar(200) DEFAULT NULL,
  signed_up datetime(6) DEFAULT NULL,
  level   bigint NOT NULL,
  player_rank varchar(200) DEFAULT NULL,
  donator  bigint NOT NULL,
  faction   bigint NULL,
  company   bigint  NULL,
  job  varchar(200) DEFAULT NULL,
  spouse   bigint  NULL,
  display_case   bigint  NULL,
  bazaar   bigint NOT NULL,
  fed   bigint NOT NULL,
  fed_reason  varchar(200) DEFAULT '' NULL,
  time_played   bigint NOT NULL,
  awards   bigint NOT NULL,
  update_on_viasnapshotapi datetime(6) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY tb_player_snapshot_staging_player_id (player_id)
) ;

