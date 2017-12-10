import config
import json
import os.path
import datetime
import ast

def sliceDetails(command):
    skill = command[7:8]
    monster = command[9:]
    result = [monster,skill]
    return result

def multiplyString(word, amount):
    result = ''
    for x in range(0, amount):
        result += word
    return result

def chat(socket, message):
    socket.send("PRIVMSG #{} :{}\r\n".format(config.CHANNEL, message).encode('utf-8'))

def whisper(socket, username, message):
    socket.send('PRIVMSG #jtv :/w {} {}\r\n'.format(username, message).encode('utf_8'))

def checkRuneList(rune_sets):
    final_sets = []
    four_sets = ['Fatal', 'Swift', 'Rage', 'Violent', 'Despair', 'Vampire']
    two_sets = ['Energy', 'Blade', 'Focus', 'Guard', 'Endure', 'Will', 'Nemesis', 'Shield', 'Revenge', 'Destroy',
                'Fight', 'Enhance', 'Accuracy', 'Determination', 'Tolerance']

    for four_set in four_sets:
        if rune_sets.count(four_set) >= 4:
            final_sets.append(four_set)

    for two_set in two_sets:
        if rune_sets.count(two_set) >= 2:
            if rune_sets.count(two_set) >= 4:
                if rune_sets.count(two_set) == 6:
                    final_sets.append(two_set)
                    final_sets.append(two_set)
                    final_sets.append(two_set)
                else:
                    final_sets.append(two_set)
                    final_sets.append(two_set)
            else:
                final_sets.append(two_set)

    if len(final_sets) == 0:
        result = 'Broken'
    else:
        result = '/'.join(final_sets)

    return result

def endingChecker(amount,word):
    if amount == 1:
        result = word
    else:
        result = word + 's'
    return result

def checkCooldown(cds,command,user,limit):
    for cooldown in cds:
        if user == cooldown[0] and command == cooldown[1]:
            now = time.time()
            then = cooldown[2]
            difference = now - then
            if difference < limit:
                return true
            else:
                return false

def getMonsterInfo(monster,path):
    if os.path.isfile(path):
        with open(path) as data_file:
            data = json.load(data_file)
        name = data['name']
        element = data['element']
        if data['is_awakened'] is True:
            stars = data['base_stars'] - 1
        else:
            stars = data['base_stars']
        star_string = multiplyString('<:star_icon_y:346034828824674305>', stars)
        awaken = data['awaken_bonus']
        if data['leader_skill'] is None:
            leader = '-'
        else:
            leader = '{0}% {1} [{2}]'.format(data['leader_skill']['amount'], data['leader_skill']['attribute'],
                                             data['leader_skill']['area'])
        stats = 'HP: {0}, Attack: {1}, Defense: {2}, SPD: {3}'.format(data['max_lvl_hp'], data['max_lvl_attack'],
                                                                      data['max_lvl_defense'], data['speed'])
        skills = []
        for skill in data['skills']:
            if skill['cooltime'] is None:
                cooldown = ''
            else:
                cooldown = '(Reusable in {} turns)'.format(skill['cooltime'])
            if skill['hits'] is None:
                hits = ''
            else:
                hitter = endingChecker(skill['hits'], 'Hit')
                hits = '[{} {}]'.format(skill['hits'], hitter)

            if skill['multiplier_formula_raw'] == '[]':
                multiplier = ''
            else:
                mult = ast.literal_eval(skill['multiplier_formula_raw'])
                multiplier = ''
                for part in mult:
                    if len(part) > 1:
                        piece = '[{}]'.format(' '.join(map(str, part)))
                    else:
                        piece = ' '.join(map(str, part))
                    multiplier += piece

                mult_dict = {'ATTACK_LOSS_HP': 'Lost HP', 'TARGET_TOT_HP': 'Enemy MAX HP',
                             'TARGET_CUR_HP_RATE': 'Enemy HP %', 'ATTACK_TOT_HP': 'MAX HP', 'ATTACK_SPEED': 'SPD',
                             'TARGET_SPEED': 'Enemy SPD', 'ATTACK_CUR_HP_RATE': 'Self HP %',
                             'ATTACK_WIZARD_LIFE_RATE': 'Surviving Allies %', 'ATTACK_LV': 'Level'}

                for word in ['ATTACK_LOSS_HP','TARGET_TOT_HP','TARGET_CUR_HP_RATE','ATTACK_WIZARD_LIFE_RATE','ATTACK_CUR_HP_RATE','ATTACK_TOT_HP','ATTACK_SPEED','TARGET_SPEED','ATTACK_LV']:
                    multiplier = multiplier.replace(word,mult_dict[word])
                if len(mult) > 3:
                    multiplier = '{}[{}]'.format(multiplier[:12],multiplier[12:])
            skillup_string = endingChecker(skill['max_level'] - 1, 'Skillup')
            skillups = '{} {}'.format(skill['max_level'] - 1, skillup_string)
            info = '{0}: {1} {2}{3}{4}[{5}]'.format(skill['name'],
                                                  skill['description'],
                                                  cooldown, multiplier,
                                                  hits, skillups)
            skills.append(info)
        skill_result = '\n'.join(skills)
        if '(' in monster:
            awaken_from = 'Unicorn'
        elif data['awakens_from'] is None:
            awaken_from = ''
        else:
            awaken_from = ' {}'.format(data['awakens_from']['name'])
        result = '**{0}** ({1}{2}) {3}\n{4}\nLeader Skill: {5}\nAwakening Bonus: {6}\n{7}'.format(name,element,awaken_from,star_string,stats,leader,awaken,skill_result)
        return result
