EMPTY=0
PLAYER_X=1
PLAYER_O=-1
MARKS={PLAYER_X:"X",PLAYER_O:"O",EMPTY:" "}
DRAW=2

import random

#ボード管理クラス
class TTTBoard:

    def __init__(self,board=None):
        if board==None:
            self.board = []
            for i in range(9):self.board.append(EMPTY)
        else:
            self.board=board
        self.winner=None

    def get_possible_pos(self):
        pos=[]
        for i in range(9):
            if self.board[i]==EMPTY:
                pos.append(i)
        return pos

    def print_board(self):
        tempboard=[]
        for i in self.board:
            tempboard.append(MARKS[i])
        row = ' {} | {} | {} '
        hr = '\n-----------\n'
        print((row + hr + row + hr + row).format(*tempboard))



    def check_winner(self):
        win_cond = ((1,2,3),(4,5,6),(7,8,9),(1,4,7),(2,5,8),(3,6,9),(1,5,9),(3,5,7))
        for each in win_cond:
            if self.board[each[0]-1] == self.board[each[1]-1]  == self.board[each[2]-1]:
                if self.board[each[0]-1]!=EMPTY:
                    self.winner=self.board[each[0]-1]
                    return self.winner
        return None

    def check_draw(self):
        if len(self.get_possible_pos())==0 and self.winner is None:
            self.winner=DRAW
            return DRAW
        return None

    def move(self,pos,player):
        if self.board[pos]== EMPTY:
            self.board[pos]=player
        else:
            self.winner=-1*player
        self.check_winner()
        self.check_draw()

    def clone(self):
        return TTTBoard(self.board.copy())

    def switch_player(self):
        if self.player_turn == self.player_x:
            self.player_turn=self.player_o
        else:
            self.player_turn=self.player_x

#ゲーム進行クラス
class TTT_GameOrganizer:

    act_turn=0
    winner=None

    def __init__(self,px,po,nplay=1,showBoard=True,showResult=True,stat=100):
        self.player_x=px
        self.player_o=po
        self.nwon={px.myturn:0,po.myturn:0,DRAW:0}
        self.nplay=nplay
        self.players=(self.player_x,self.player_o)
        self.board=None
        self.disp=showBoard
        self.showResult=showResult
        self.player_turn=self.players[random.randrange(2)]
        self.nplayed=0
        self.stat=stat

    def progress(self):
        while self.nplayed<self.nplay:
            self.board=TTTBoard()
            while self.board.winner==None:
                if self.disp:print("Turn is "+self.player_turn.name)
                act=self.player_turn.act(self.board)
                self.board.move(act,self.player_turn.myturn)
                if self.disp:self.board.print_board()

                if self.board.winner != None:
                    # notice every player that game ends
                    for i in self.players:
                        i.getGameResult(self.board)
                    if self.board.winner == DRAW:
                        if self.showResult:print ("Draw Game")
                    elif self.board.winner == self.player_turn.myturn:
                        out = "Winner : " + self.player_turn.name
                        if self.showResult: print(out)
                    else:
                        print ("Invalid Move!")
                    self.nwon[self.board.winner]+=1
                else:
                    self.switch_player()
                    #Notice other player that the game is going
                    self.player_turn.getGameResult(self.board)

            self.nplayed+=1
            if self.nplayed%self.stat==0 or self.nplayed==self.nplay:
                 print(self.player_x.name+":"+str(self.nwon[self.player_x.myturn])+","+self.player_o.name+":"+str(self.nwon[self.player_o.myturn])
             +",DRAW:"+str(self.nwon[DRAW]))


    def switch_player(self):
        if self.player_turn == self.player_x:
            self.player_turn=self.player_o
        else:
            self.player_turn=self.player_x

#プレイヤーQ-learning
class PlayerQL:
    def __init__(self,turn,name="QL",e=0.2,alpha=0.3):
        self.name=name
        self.myturn=turn
        self.q={} #set of s,a
        self.e=e
        self.alpha=alpha
        self.gamma=0.9
        self.last_move=None
        self.last_board=None
        self.totalgamecount=0


    def policy(self,board):
        self.last_board=board.clone()
        acts=board.get_possible_pos()
        #Explore sometimes
        if random.random() < (self.e/(self.totalgamecount//10000+1)):
                i=random.randrange(len(acts))
                return acts[i]
        qs = [self.getQ(tuple(self.last_board.board),act) for act in acts]
        maxQ= max(qs)

        if qs.count(maxQ) > 1:
            # more than 1 best option; choose among them randomly
            best_options = [i for i in range(len(acts)) if qs[i] == maxQ]
            i = random.choice(best_options)
        else:
            i = qs.index(maxQ)

        self.last_move = acts[i]
        return acts[i]

    def getQ(self, state, act):
        # encourage exploration; "optimistic" 1.0 initial values
        if self.q.get((state, act)) is None:
            self.q[(state, act)] = 1
        return self.q.get((state, act))

    def getGameResult(self,board):
        r=0
        if self.last_move is not None:
            if board.winner is None:
                self.learn(self.last_board,self.last_move, 0, board)
                pass
            else:
                if board.winner == self.myturn:
                    self.learn(self.last_board,self.last_move, 1, board)
                elif board.winner !=DRAW:
                    self.learn(self.last_board,self.last_move, -1, board)
                else:
                    self.learn(self.last_board,self.last_move, 0, board)
                self.totalgamecount+=1
                self.last_move=None
                self.last_board=None

    def learn(self,s,a,r,fs):
        pQ=self.getQ(tuple(s.board),a)
        if fs.winner is not None:
            maxQnew=0
        else:
            maxQnew=max([self.getQ(tuple(fs.board),act) for act in fs.get_possible_pos()])
        self.q[(tuple(s.board),a)]=pQ+self.alpha*((r+self.gamma*maxQnew)-pQ)
        #print (str(s.board)+"with "+str(a)+" is updated from "+str(pQ)+" refs MAXQ="+str(maxQnew)+":"+str(r))
        #print(self.q)


    def act(self,board):
        return self.policy(board)

#プレイヤーモンテカルロ
class PlayerMC:
    def __init__(self,turn,name="MC"):
        self.name=name
        self.myturn=turn

    def getGameResult(self,winner):
        pass

    def win_or_rand(self,board,turn):
        acts=board.get_possible_pos()
        #see only next winnable act
        for act in acts:
            tempboard=board.clone()
            tempboard.move(act,turn)
            # check if win
            if tempboard.winner==turn:
                return act
        i=random.randrange(len(acts))
        return acts[i]

    def trial(self,score,board,act):
        tempboard=board.clone()
        tempboard.move(act,self.myturn)
        tempturn=self.myturn
        while tempboard.winner is None:
            tempturn=tempturn*-1
            tempboard.move(self.win_or_rand(tempboard,tempturn),tempturn)

        if tempboard.winner==self.myturn:
            score[act]+=1
        elif tempboard.winner==DRAW:
            pass
        else:
            score[act]-=1


    def getGameResult(self,board):
        pass


    def act(self,board):
        acts=board.get_possible_pos()
        scores={}
        n=50
        for act in acts:
            scores[act]=0
            for i in range(n):
                #print("Try"+str(i))
                self.trial(scores,board,act)

            #print(scores)
            scores[act]/=n

        max_score=max(scores.values())
        for act, v in scores.items():
            if v == max_score:
                #print(str(act)+"="+str(v))
                return act

pQ=PlayerQL(PLAYER_O,"QL1")
p2=PlayerQL(PLAYER_X,"QL2")
game=TTT_GameOrganizer(pQ,p2,100000,False,False,10000)
game.progress()
