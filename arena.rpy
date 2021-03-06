## This file defines Actor and Arena class to add turn-based combat.
## ターン制の戦闘や競争を行うためのアクタークラスとアリーナクラスを追加するファイルです。
## 基本的な枠組みしかありませんので、実用には改変する必要があります。

##############################################################################
## How to Use
##############################################################################

## まずアクターが使用する能力を Skill(name, type, effect, target, value, score, cost) で定義します。
## type は表示される能力のカテゴリーです。このデモでは "active" のみ有効です。
## effect は使用した時の効果です。"attack", "heal" 以外は Arena クラスに書き加えます。
## target は能力を使う相手で "friend" か "foe" があります。
## value は効果の能力を使用した時の効果の強さです。
## score, cost は使用回数がある能力に使います。デフォルトは1と0です。
## skill の名前空間も使えます。

define skill.attack = Skill("Attack", type="active", effect="attack", target="foe", value=5)
define skill.heal = Skill("Heal", type="active", effect="heal", target="friend", value=10, score=2, cost=1)

## 次にアクターを Actor(name, skills, hp) で定義します。
## skills は能力のリストで、skill. を外した文字列です。
## hp は能力値です。Actor クラスを書き換えることで追加できます。

default knight = Actor("Knight", skills=["attack"], hp=20)
default bishop = Actor("Bishop", skills=["attack", "heal"], hp=15)
default pawn = Actor("Pawn A", skills=["attack"], hp=10)

## actor.copy(name) で同じ能力のアクターを名前を変えてコピーします。
default pawn2 = pawn.copy("Pawn B")
default pawn3 = pawn.copy("Pawn C")

## 最後に戦闘に関するデータを保存するアリーナを定義します。
default arena = Arena()

## 以上で準備完了です。


## ゲームがスタートしたら jump sample_combat でここに飛んでください。

label sample_combat:

    ## 戦闘仲間と戦闘相手のアクターをリストとしてアリーナに追加します。

    $ arena.player_actors = [knight, bishop]
    $ arena.enemy_actors = [pawn, pawn2, pawn3]

    ## ここから戦闘開始。
    call _combat(arena)

    ## 戦闘が終わると結果を _return で知ることができます。
    if _return == "win":
         "You win"

    elif _return == "lose":
        "You lose"

    else:
        "Draw"

    return


##############################################################################
## Definition
##############################################################################

##############################################################################
## Combat label

label _combat(arena):

    # initialize
    python:
        arena.init()
        _rollback = False
                
    show screen combat_ui(arena)

    while arena.state not in ["win", "lose", "draw"]:

        python:

            # set current actor to perform
            arena.actor = arena.get_turn()

            # player 
            if arena.actor in arena.player_actors:
                arena.actor.skill = renpy.call_screen("choose_skill", arena)
                arena.actor.target = renpy.call_screen("choose_target", arena)
                
            # enemy
            else:
                arena.actor.skill = arena.get_skill()
                arena.actor.target = arena.get_target()

            # perform skill
            arena.perform_skill()

            # update arena's state
            arena.end_turn()

    hide screen combat_ui
    
    python:
        _return = arena.state
        arena.reset_state()
        _rollback = True
        renpy.block_rollback()
        
    return _return


##############################################################################
## combat screens

screen combat_ui(arena):

    zorder -1

    # show player status
    vbox:
        for i in arena.player_actors:
            hbox:
                text "[i.name]: HP [i.hp]"

    # show enemy status
    vbox xalign 1.0:
        for i in arena.enemy_actors:
            hbox:
                text "[i.name]: HP [i.hp]"


screen choose_skill(arena):

    tag menu
    modal True
    
    $ actor = arena.actor

    # caption
    label "[actor.name]'s turn" align .5, .2

    # commands
    vbox align .5, .5:
        for name, score, obj in actor.get_skills(types=["active"]):
            $ score_text = " ({}/{})".format(score, obj.score) if obj.cost else "" 
            textbutton "[obj.name][score_text]":
                
                # sensitive if skill is available
                if arena.check_skill(actor, name):
                    action Return(name)
                    

screen choose_target(arena):

    tag menu
    modal True

    $ actor = arena.actor
    
    # caption
    label "Choose target" align .5, .2

    # commands
    vbox align .5, .5:
        for i in arena.foes(actor) if actor.get_skill(actor.skill).target == "foe" else arena.friends(actor):
            textbutton i.name:
                
                # sensitive if target is available
                if arena.check_target(actor, i):
                    action Return(i)


##############################################################################
## Arena class.

init -3 python:

    class Arena(object):

        """
        This class represents acting field for actors. It has the follwing fields:

        player_actors - list of playable actors
        enemy_actors - list of unplayable actors
        actor - current actor to perform
        order - performing order of actors 
        state - curernt state of arena. "win", "lose", "draw" ends combat, otherwise keep performing.
        """

        def __init__(self, player_actors=None, enemy_actors=None):

            self.player_actors = player_actors or []
            self.enemy_actors = enemy_actors or []

            self.order = []
            self.actor = None
            self.state = None
            
            
        def friends(self, actor=None):
            # returns friendly actors
            
            actor = actor or self.actor
            return self.player_actors if actor in self.player_actors else self.enemy_actors
            
                
        def foes(self, actor=None):
            # returns hostile actors
            
            actor = actor or self.actor
            return self.player_actors if actor in self.enemy_actors else self.enemy_actors


        def init(self):
            # call this to set order

            self.state = None
            self.order = self.player_actors + self.enemy_actors
            renpy.random.shuffle(self.order)


        def reset_state(self):
            # reset actors's states

            for i in self.player_actors + self.enemy_actors:
                i.reset_state()


        def get_turn(self):
            # returns a next actor to perform

            while True:
                actor = self.order.pop(0)
                self.order.append(actor)
                if actor.hp > 0:
                    return actor
                    
                    
        def check_skill(self, actor=None, name=None):
            # returns True if skill is available
            
            actor = actor or self.actor
            name = name or actor.skill
            obj = actor.get_skill(name)
            if obj.cost == 0 or actor.count_skill(name) >= obj.cost:
                return True
                
                
        def get_skill(self, actor=None):
            # returns a random skill name

            actor = actor or self.actor
            names = [x for x in actor.get_skills(score=1, types=["active"], rv="name") if self.check_skill(actor, x)]
            return  renpy.random.choice(names)
            
                
        def check_target(self, actor=None, target=None):
            # returns True if target is available
            
            actor = actor or self.actor
            target = target or actor.target
            if target.hp>0:
                return True
                
                
        def get_target(self, actor=None):
            # returns a random target

            actor = actor or self.actor
            targets = self.foes(actor) if actor.get_skill(actor.skill).target == "foe" else self.friends(actor)
            targets = [x for x in targets if self.check_target(actor, x)]
            return renpy.random.choice(targets)


        def perform_skill(self, actor=None, target=None, name=None):
            # perform skill on the target
            
            actor = actor or self.actor            
            target = target or actor.target
            name = name or actor.skill
            obj = actor.get_skill(name)

            if obj.effect == "attack":
                target.change_state(hp = -obj.value)
                narrator ("{}'s attack. {} loses {} HP".format(actor.name, target.name, obj.value))

            elif obj.effect == "heal":
                target.change_state(hp = +obj.value)
                narrator ("{}'s heal. {} gains {} HP".format(actor.name, target.name, obj.value))
            
            if obj.cost:
                actor.score_skill(actor.skill, - obj.cost, remove=False)


        def end_turn(self):
            # call this each turn to update arena's state

            for i in self.player_actors:
                if i.hp > 0:
                    break
            else:
                self.state = "lose"

            for i in self.enemy_actors:
                if i.hp > 0:
                    break
            else:
                self.state = "win"
                

##############################################################################
## Actor class.

    from collections import OrderedDict

    class Actor(object):

        """
        Class that performs skills. It has follwing fields:

        name - name of this actor
        skills - dict of {"skillname", score}
        attributes - float or int variables that are added into an actor when an object is created.
        default_attrributes - default values of attributes. if it's positive number, it means maximum point.
        """

        # Default attributes that are added when attributes are not defined.
        # This will create self.hp and self.default_hp.
        _attributes = ["hp"]
        
        # Default skill categories. It's used when skill_types are not defined.
        _skill_types = ["active"]

        def __init__(self, name="", skills=None, skill_types = None, **kwargs):

            self.name = name
            self.skills = OrderedDict()
            if skills:
                for i in skills:
                    self.add_skill(i)            
            self.skill_types = skill_types or self._skill_types
            
            self.skill = None
            self.target = None

            # creates attributes as field value
            for i in self._attributes:
                if i in kwargs.keys():
                    setattr(self, "default_"+i, kwargs[i])
                    setattr(self, i, kwargs[i])
                else:
                    setattr(self, "default_"+i, None)
                    setattr(self, i, None)


        def copy(self, name=None):
            # Returns copy of actor, changing its name.

            from copy import deepcopy

            actor = deepcopy(self)
            if name:
                actor.name = name

            return actor


        def reset_state(self):
            # reset attributes

            for i in self._attributes:
                setattr(self, i, getattr(self, "default_"+i))

            self.skill = None
            self.target = None


        def change_state(self, **kwargs):
            # Change attribtues. 
            # instead of changing attributes directly, use this method.

            for k, v in kwargs.items():
                if k in self._attributes:
                    nv = getattr(self, k) + v
                    mv = getattr(self, "default_"+k)
                    setattr(self, k, max(0, min(nv, mv)))
                else:
                    raise Exception("{} is not defined attributes".format(k))
            

        @classmethod
        def get_skill(self, name):
            # returns skill object from name

            if isinstance(name, Skill): 
                return name
                
            elif isinstance(name, basestring):
                obj = getattr(store.skill, name, None) or getattr(store, name, None)
                if obj: 
                    return obj
                
            raise Exception("Skill '{}' is not defined".format(name))
                        

        def has_skill(self, name, score=None):
            # returns True if actor has this skill whose score is higher than given.
            
            # check valid name or not
            self.get_skill(name)

            return name in [k for k, v in self.skills.items() if score==None or v >= score]
            

        def has_skills(self, name, score=None):
            # returns True if actor has these skills whose score is higher than give. 
            # "a, b, c" means a and b and c, "a | b | c" means a or b or c.
            
            separator = "|" if name.count("|") else ","
            names = name.split(separator)
            for i in names:
                i = i.strip()
                if separator == "|" and self.has_item(i, score):
                    return True
                elif separator == "," and not self.has_item(i, score):
                    return False
                    
            return True if separator == ","  else False
            

        def count_skill(self, name):
            # returns score of this skill
            
            if self.has_skill(name):
                return self.skills[name]
                
            
        def get_skills(self, score=None, types = None, rv=None):
            # returns list of (name, score, object) tuple in conditions
            # if rv is "name" or "obj", it returns them.
            
            skills = [k for k, v in self.skills.items() if score==None or v >= score]
            
            if types:
                skills = [i for i in skills if self.get_skill(i).type in types]
                
            if rv == "name":
                return skills
                
            elif rv == "obj":
                return [self.get_skill(i) for i in skills]
                
            return  [(i, self.skills[i], self.get_skill(i)) for i in skills]


        def add_skill(self, name, score = None):
            # add an skill
            # if score is given, this score is used instead of skill's default value.
            
            score = score or self.get_skill(name).score

            if self.has_skill(name):
                self.skills[name] += score
            else:
                self.skills[name] = score


        def remove_skill(self, name):
            # remove an skill

            if self.has_skill(name):
                del self.skills[name]


        def score_skill(self, name, score, remove = True):
            # changes score of name
            # if remove is True, skill is removed when score reaches 0

            self.add_skill(name, score)
            if remove and self.skills[name] <= 0:
                self.remove_skill(name)  


        def replace_skills(self, first, second):
            # swap order of two slots

            keys = list(self.skills.keys())
            values = list(self.skills.values())
            i1 = keys.index(first)
            i2 = keys.index(second)
            keys[i1], keys[i2] = keys[i2], keys[i1]
            values[i1], values[i2] = values[i2], values[i1]
            
            self.skills = OrderedDict(zip(keys, values))


        def sort_skills(self, order="name"):
            # sort slots
            
            skills = self.skills.items()

            if order == "name":
                skills.sort(key = lambda i: self.get_skill(i[0]).name)
            elif order == "type":
                skills.sort(key = lambda i: self.skill_types.index(self.get_skill(i[0]).type))
            elif order == "value":
                skills.sort(key = lambda i: self.get_skill(i[0]).value, reverse=True)
            elif order == "amount":
                skills.sort(key = lambda i: i[1], reverse=True)
                
            self.skills = OrderedDict(skills)


        def get_all_skills(self, namespace=store):
            # get all skill objects defined under namespace

            for i in dir(namespace):
                if isinstance(getattr(namespace, i), Skill):
                    self.add_skill(i)



##############################################################################
## Skill class.

    class Skill(object):

        """
        Class that represents skill that is stored by actor object. It has follwing fields:

        name - skill name that is shown on the screen
        type - skill category
        effect - effect on use.
        target - target of skill. if not "friend", "foe" is default
        value - quality of skill
        score - default amount of skill when it's added into actor
        cost - if not zero, using this skill reduces score.
        info - description that is shown when an skill is focused
        """


        def __init__(self, name="", type="", effect="", target="foe", value=0, score=1, cost=0, info=""):

            self.name = name
            self.type = type
            self.effect = effect
            self.target = target
            self.value = int(value)
            self.score = int(score)
            self.cost = int(cost)
            self.info = info
            
            
##############################################################################
## Create namespace

init -999 python in skill:
    pass



