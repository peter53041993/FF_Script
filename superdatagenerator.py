from typing import Dict, List
import cx_Oracle
import random
import requests
import json

from requests.sessions import session
import super_betcontent

class Super2000Data:
        
    # get connection to Oracle Database.
    def oracle(self, env: int) -> object:
        '''
        param: env -> envirment for DB, {0: dev02, 1: 188, 2: product}
        return cx_Oracle <class>
        '''
        if env == 2:
            username = 'rdquery'
            service_name = 'gamenxsXDB'
        else:
            username = 'firefog'
            service_name = ''

        oracle_ = {
            'password':['LF64qad32gfecxPOJ603', 'JKoijh785gfrqaX67854', 'eMxX8B#wktFZ8V'],
            'ip':['10.13.22.161', '10.6.1.41', '10.6.1.31'],
            'sid':['firefog', 'game',''],
            }
        
        password = oracle_['password'][env]
        host = oracle_['ip'][env]+':1521/'+oracle_['sid'][env]+service_name
        # host = f"{oracle_['ip'][env]}:1521/{oracle_['sid'][env]}{service_name}"

        conn = cx_Oracle.connect(username, password, host)
        
        return conn
    
    # get lottery list for super2000 from DB.
    def getLottery(self, env: int, lottery_type: int) -> list:
        '''
        param1: conn is retuen by fuction "oracle"
        param2: lottery type number, see { lottery_type_dict } below
        return: list for searching lotterys
        '''
        lottery_type_dict = {
            0: '时时彩',
            1: '11选5',
            2: '快三',
            3: '国际彩',
            4: '3D/低频',
            5: '趣味彩',
        }

        lottery_type = lottery_type_dict[lottery_type]

        sql = f'''select
                    LOTTERYID
                from
                    GAME_SERIES
                where
                    LOTTERY_FRONT_TYPE = '{lottery_type}'              
        '''

        lottery_list = []
        conn = self.oracle(env)
        with conn.cursor() as cursor:

            cursor.execute(sql)
            rows = cursor.fetchall()
            
            for i in rows:
                lottery_list.append(int(i[0]))

        conn.close

        lottery_data = super_betcontent.lottery_all
        for i in lottery_list:
            if len(lottery_data[i]) < 4:
                lottery_list.remove(i)

        return lottery_list
    
    def saleSwitch(self, env: int, status: str, *lottery_type: str) -> None:
        '''
        param1: env, 0: dev02, 1:188
        param2: status, 'N' for all avaliable, 'Y' for all unavaliable
        param*: lottery_type, 时时彩、11选5、快三、国际彩、3D/低频、趣味彩
        return: None
        '''
        if not lottery_type:
            sql = f'''update
                        game_series
                    set
                        IS_TEMP_STOP_SALE = '{status}'
                '''
        else:
            sql = f'''update
                        game_series
                    set
                        IS_TEMP_STOP_SALE = '{status}'
                    where
                        LOTTERY_FRONT_TYPE = '{lottery_type[0]}'
                '''
        

        conn = self.oracle(env)
        with conn.cursor() as cursor:

            cursor.execute(sql)

        conn.commit()
        conn.close()

        return None

    def selectUserid(self, env: int, user: str) -> int:
        '''
        param1: env
        param2: user, account, for example: peter001
        return: userid, is int, for example: 100100
        '''
        conn = self.oracle(env)
        with conn.cursor() as cursor:
            sql = f'''select
                        id
                    from
                        user_customer
                    where
                        account = '{user}'
            '''
            cursor.execute(sql)
            rows = cursor.fetchall()
            if len(rows) != 0: 
                userid = rows[0][0]

                return userid
            else:
                print('User does not existed, please check again')

        conn.close()
        
    
    def selectFundid(self, env: int, user: str) -> dict:
        '''
        param1: env
        param2: user, account, for example: peter001
        return: dict, see output formate
        '''
        conn = self.oracle(env)
        with conn.cursor() as cursor:
            sql = f'''select
                        id, type_id
                    from
                        FUND_MANUAL_DEPOSIT
                    where
                        approve_time is null and 
                        rcv_account = '{user}' and
                        apply_time > trunc(sysdate,'mm')
                    order by
                        APPLY_TIME desc
            '''
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            fund_dict = {}
            for index, value in enumerate(rows):
                fund_dict[index] = value
            
        conn.close()
        return fund_dict # output: { index: (fundid, fund_type), ... }

    # searching issueName and issueCode
    def select_issue(self, env: int, lotteryid: int) -> tuple: 
        #Joy188Test.date_time()
        #today_time = '2019-06-10'#for 預售中 ,抓當天時間來比對,會沒獎期
        '''
        param1: env -> envirment for DB, {0: dev02, 1: 188, 2: product} 
        param2: lotteryid in DB, for example: 99112
        retrun: tuple inculde (issueName, issue), for example: ("20210713-16", 20210713103016)
        '''
        conn = self.oracle(env)
        try:
            with conn.cursor() as cursor:
                #sql = "select web_issue_code,issue_code from game_issue where lotteryid = '%s' and sysdate between sale_start_time and sale_end_time"%(lotteryid)
                
                # 休市查詢槳期用
                sql = "select web_issue_code,issue_code from game_issue where lotteryid = '%s' and sysdate < sale_end_time" % lotteryid
                cursor.execute(sql)
                rows = cursor.fetchall()

                issueName = []
                issue = []
                if lotteryid in [99112, 99306]:#順利秒彩,順利11選5  不需 講期. 隨便塞
                    issueName.append(1)
                    issue.append(1)
                else:
                    for i in rows:# i 生成tuple
                        issueName.append(i[0])
                        issue.append(i[1])
            conn.close()
        except:
            pass

        return (issueName, issue) # output: tuple(list, lsit)

    def adminLogin(self, env: int) -> None:
        '''
        param: env, 0: dev02, 1: 188
        return: None (get admin header and cookies)
        '''
        global admin_header, admin_url
        global cookies

        admin_dict = {
            0:'http://admin.dev02.com', 
            1:'http://admin.joy188.com'
            }
        
        admin_url = admin_dict[env]
        url = f'{admin_url}/admin/login/login'

        admin_header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.100 Safari/537.36', 
            'Content-Type': 'application/x-www-form-urlencoded'
                  }
        
        password = '123qwe' if env == 0 else 'amberrd'
        admin_data = {
            'username':'cancus', 
            'password': password, 
            'bindpwd':123456
            }

        # sent Request to Admin backplatform
        session = requests.Session()
        res = session.post(url, data= admin_data, headers= admin_header)

        # Maybe needs JSON decode ? (two lines below)
        decoded_data = res.text.encode().decode('utf-8-sig')
        data = json.loads(decoded_data)

        if data['isSuccess'] == 1:
            print(f'Success to Login Admin: {admin_dict[env]}')
        else:
            print(f'Fail to Login Admin: {admin_dict[env]}')

        # get cookies and add to admin header
        cookies = res.cookies.get_dict()
        admin_header['ANVOAID'] = cookies['ANVOAID']

        return None
    
    def addRsason(self, env: int , user: str, fund_type: int, cost: float) -> None:
        '''
        param1: env
        param2: account
        param3: fund_type refer to 後台-資金-新建人工單
        param4: number of amount changing(inculde increase and decrease)
        return: None
        '''
        userid = self.selectUserid(env, user)
        url = f'{admin_url}/admin/Opterators/index?parma=opter1'

        # global admin_header not allow here 
        header = {
            'Cookie': f"ANVOAID={cookies['ANVOAID']}",
            'Accept':'application/json, text/javascript, */*; q=0.01',
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'
         }
        header['User-Agent'] = admin_header['User-Agent']


        data = f'rcvAct={user}&depositAmt={cost}&memo=test&id=&userId={userid}&sSelectValue={fund_type}&note=test&chargeSn='

        session = requests.Session()

        if fund_type in [10, 12, 13]: # reasons about pt
            print('pt is producted, dont use it!!')
            pass
        elif fund_type in [32, 33, 34]: # reasons about ag 
            print('ag is producted, dont use it!!')
            pass
        else:
            res = session.post(url, data= data, headers= header)
        
            if res.json()['status'] == 'ok':
                print(f'{user}： reason {fund_type} build successfully!!')
            else:
                print(f'{user} fail to build reason')
        
        return None

    def confirmReason(self, env: int, user: str, status: int) -> None:
        '''
        param1: env
        param2: account
        param3: status, 1: pass, 2: deny
        return: None
        '''
        session = requests.Session()

        url = f'{admin_url}/admin/Opterators/index?parma=sv2'

        # global admin_header not allow here 
        header = {
            'Cookie': f"ANVOAID={cookies['ANVOAID']}",
            'Accept':'application/json, text/javascript, */*; q=0.01',
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'
         }
        header['User-Agent'] = admin_header['User-Agent']

        fundid_dict = self.selectFundid(env, user)
        for key in fundid_dict.keys():
            fund_id = fundid_dict[key][0]
            fund_type = fundid_dict[key][1]
            
            data = f'id={fund_id}&status={status}&typeId={fund_type}'
            
            res = session.post(url, data= data, headers= header)

            if res.json()['status'] == 'ok':
                print(f'{user}： reason {fund_type} confirm successfully!!')
            else:
                print(f'{user} fail to confirm reason')

        return None
    
    def getUserAmount(self, env: int, user: str) -> float:
        '''
        param1: env, 0: dev02, 1: 188
        param2: user, account
        return: avilible amount now
        '''
        conn = self.oracle(env)
        with conn.cursor() as cursor:
            sql = f'''select 
                        CT_BAL
                    FROM
                        (select
                            CT_BAL, account
                        from
                            FUND_CHANGE_LOG
                                inner join user_customer on FUND_CHANGE_LOG.USER_ID = user_customer.id
                        order by
                            GMT_CREATED desc)
                    where
                        account = '{user}' and rownum = 1
            '''
            cursor.execute(sql)
            rows = cursor.fetchall()

            amount = rows[0][0]
            amount = amount / 10000

        return amount

    def autoDeposit(self, env: int, user: str, amount: float) -> None:
        '''
        param1: env, 0: dev02, 1: 188
        param2: user is account
        param3: number of amount inceeasing
        return: None
        '''
        self.addRsason(env, user, 7, amount) # fund_type is 7, for 人工加幣
        self.confirmReason(env, user, 1) # status is 1, for pass

        return None
    
    def getAwardGroupID(self, env: int, lotteryid: int) -> int:
        

        return

    # creat ball data (All gameplay)
    def ballContentAll2000(self, env: int, lotteryid: int, moneyunit: float, awardMode: int) -> dict:
        '''
        param1: env -> envirment for DB, {0: dev02, 1: 188, 2: product}
        param2: lotteryid in DB, for example: 99112
        param3: moneyunit for unit 1 or 0.1 (CNY)
        param4: awardMode for normal: 1, high: 2
        return: list for ballcontent(All gameplay)
        '''
        balls = super_betcontent.all_gameplay['balls_2000']
        bet_params = super_betcontent.bet_params
        lottery_2000 = super_betcontent.lottery_2000

        cost = 0
        for i in balls:
            i['id'] = random.randint(0, 100)
            i['moneyunit'] = moneyunit
            i['awardMode'] = awardMode
            cost_singl = i['moneyunit'] * i['multiple'] * i['num'] * 2
            cost += cost_singl
        
        issue = self.select_issue(env, lotteryid)

        bet_params['gameType'] = lottery_2000[lotteryid][1]
        bet_params['orders'][0]['number'] = issue[0][0]
        bet_params['orders'][0]['issueCode'] = issue[1][0]
        bet_params['amount'] = cost
        bet_params['balls'] = balls

        return bet_params

    # creat ball data (Each gameplay)
    def ballContentSingle2000(self, env: int, lotteryid: int, moneyunit: float, awardMode: int) -> list:
        '''
        param1: env -> envirment for DB, {0: dev02, 1: 188, 2: product} 
        param2: lotteryid in DB, for example: 99112
        param3: moneyunit for unit 1 or 0.1 (CNY)
        param4: awardMode for normal: 1, high: 2 
        return: list for ballcontent(single gameplay)
        '''
        balls = super_betcontent.all_gameplay['balls_2000']
        bet_params = super_betcontent.bet_params
        lottery_2000 = super_betcontent.lottery_2000

        bet_list = []

        issue = self.select_issue(env, lotteryid)

        for i in balls:
            i['id'] = random.randint(0, 100)
            i['moneyunit'] = moneyunit
            i['awardMode'] = awardMode
            cost = i['moneyunit'] * i['multiple'] * i['num'] * 2

            bet_params['gameType'] = lottery_2000[lotteryid][1]
            bet_params['orders'][0]['number'] = issue[0][0]
            bet_params['orders'][0]['issueCode'] = issue[1][0]
            bet_params['amount'] = cost
            bet_params['balls'] = [i]

            result = bet_params.copy()

            bet_list.append(result)
        
        return bet_list # output is list inculde individual bet content(dict)


    def ballContentAll(self, env: int, lotteryid: int, moneyunit: float, awardMode: int) -> list:
        '''
        param1: env -> envirment for DB, {0: dev02, 1: 188, 2: product}
        param2: lotteryid in DB, for example: 99112
        param3: moneyunit for unit 1 or 0.1 (CNY)
        param4: awardMode for normal: 1, high: 2
        return: list for ballcontent(All gameplay)
        '''
        bet_params = super_betcontent.bet_params
        lottery_dict = super_betcontent.lottery_all
        balls_list = super_betcontent.lottery_all[lotteryid][3]
        
        game_content = []
        for play in balls_list:
            balls = super_betcontent.all_gameplay[play]
            cost = 0
            for i in balls:
                i['id'] = random.randint(0, 100)
                i['moneyunit'] = moneyunit
                i['awardMode'] = awardMode
                cost_singl = i['moneyunit'] * i['multiple'] * i['num'] * 2
                cost += cost_singl
            
            issue = self.select_issue(env, lotteryid)

            bet_params['gameType'] = lottery_dict[lotteryid][1]
            bet_params['orders'][0]['number'] = issue[0][0]
            bet_params['orders'][0]['issueCode'] = issue[1][0]
            bet_params['amount'] = cost
            bet_params['balls'] = balls

            game_content.append(bet_params)

        return game_content # output -> list: [ { gameplay1 }, { gameplay2 }, ... ]

    def ballContentSingle(self, env: int, lotteryid: int, moneyunit: float, awardMode: int) -> list:
        '''
        param1: env -> envirment for DB, {0: dev02, 1: 188, 2: product}
        param2: lotteryid in DB, for example: 99112
        param3: moneyunit for unit 1 or 0.1 (CNY)
        param4: awardMode for normal: 1, high: 2
        return: list for ballcontent
        '''
        bet_params = super_betcontent.bet_params
        lottery_dict = super_betcontent.lottery_all
        balls_list = super_betcontent.lottery_all[lotteryid][3]
        
        game_content = []
        for play in balls_list:
            balls = super_betcontent.all_gameplay[play]
            game_content_single = []
            for i in balls:
                
                i['id'] = random.randint(0, 100)
                i['moneyunit'] = moneyunit
                i['awardMode'] = awardMode
                cost = i['moneyunit'] * i['multiple'] * i['num'] * 2
            
                issue = self.select_issue(env, lotteryid)

                bet_params['gameType'] = lottery_dict[lotteryid][1]
                bet_params['orders'][0]['number'] = issue[0][0]
                bet_params['orders'][0]['issueCode'] = issue[1][0]
                bet_params['amount'] = cost
                bet_params['balls'] = [i]
                
                # copy a same dict for list appended, if not to using copy, will get the last dict data(because this dict iterated)
                result = bet_params.copy()
                 
                game_content_single.append(result)

            game_content.append(game_content_single)

        return game_content # output -> list: [ [{ game1_order1 }, { game1_order2 }, ... ], [{ game2_order1 }, { game2_order2 }, ... ], ... ]
    
    
    
    
