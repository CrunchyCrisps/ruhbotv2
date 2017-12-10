import ast
import json
import time
import discord
import asyncio
import urlfetch
import requests
import sqlite3
import datetime
import os.path
import random
import config
import logging
from io import BytesIO
from PIL import Image
from decimal import Decimal
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utility import sliceDetails, multiplyString, checkRuneList, endingChecker, getMonsterInfo

description = 'Discord Bot for Summoners War and Twitch.'
bot = commands.Bot(command_prefix='!', description=description)
conn = sqlite3.connect('C:\\Users\\Raffael\\Documents\\ruhBot\\users.db')
db = conn.cursor()
old_notices = []
sched = AsyncIOScheduler()
logging.basicConfig(level=logging.INFO)

async def checkHive():
    req = requests.get('https://withhive.com/api/help/notice_list/1')
    response = req.json()
    for notice in response['result']:
        if notice['GameName'] == 'Summoners War' and notice['NoticeId'] not in old_notices:
            result = '**New Notice: {} ({})**\nLink: https://withhive.com/help/notice_view/{}'.format(notice['Title'],notice['StartTime_Ymd'],notice['NoticeId'])
            old_notices.append(notice['NoticeId'])
            for guild in bot.guilds:
                channel = bot.get_guild(guild.id).system_channel
                if channel is not None:
                    await channel.send(result)

@bot.event
async def on_ready():
    print("I'm charged and ready!")
    print('-------------------------')
    sched.add_job(checkHive, 'interval', hours=3)
    sched.start()

@bot.command(help='Links your Discord account to your Swarfarm account.')
async def set(ctx, name):
    discord_id = ctx.message.author.id
    db.execute('SELECT id FROM usernames WHERE id=?', (discord_id,))
    result = db.fetchone()
    if result is None:
        db.execute('INSERT INTO usernames VALUES (?,?)', (discord_id, name))
        msg = '{} was added as your Swarfarm account.'.format(name)
    else:
        db.execute('UPDATE usernames SET swarfarm = ? WHERE id = ?', (name, discord_id))
        msg = 'Successfully updated your Swarfarm account.'.format(name)
    conn.commit()
    await ctx.send(msg)

@bot.command(help='Returns stats and skills of specified monster.')
async def mon(ctx, *monster):
    monster_fmt = ' '.join(monster).title()
    result = ''
    if any(x in monster_fmt for x in ['Wind', 'Water', 'Fire', 'Dark', 'Light']):
        #tmp_path = '/home/pi/Documents/ruhbot/monsters/{}.json'.format(monster_fmt)
        tmp_path = 'C:\\Users\\Raffael\\Documents\\ruhBot\\monsters\\{}.json'.format(monster_fmt)
        if os.path.isfile(tmp_path):
            with open(tmp_path) as data_file_tmp:
                data_tmp = json.load(data_file_tmp)
            monster_fmt = data_tmp['awakens_to']['name']

    #path = '/home/pi/Documents/ruhbot/monsters/{}.json'.format(monster_fmt)
    path = 'C:\\Users\\Raffael\\Documents\\ruhBot\\monsters\\{}.json'.format(monster_fmt)
    if os.path.isfile(path):
        result = getMonsterInfo(monster, path)
    else:
        found = False
        #mon_dir = '/home/pi/Documents/ruhbot/monsters'
        mon_dir = 'C:\\Users\\Raffael\\Documents\\ruhBot\\monsters'
        for file in os.listdir(mon_dir):
            if monster_fmt.lower() in file.lower() and found is False:
                if any(x in monster_fmt for x in ['Wind', 'Water', 'Fire', 'Dark', 'Light']):
                    #with open('/home/pi/Documents/ruhbot/monsters/{}'.format(file)) as temp_file:
                    with open('C:\\Users\\Raffael\\Documents\\ruhBot\\monsters\\{}'.format(file)) as temp_file:
                        temp_data = json.load(temp_file)
                    awakened_name = temp_data['awakens_to']['name']
                    result = getMonsterInfo(awakened_name, '{}\\{}.json'.format(mon_dir, awakened_name))
                else:
                    result = getMonsterInfo(file[:-5], '{}\\{}'.format(mon_dir, file))
                found = True
        if result == '':
            result = 'Monster not found. Try again.'
    await ctx.send(result)

@bot.command(help='Returns stats of your monster.')
async def my(ctx, *monster: str):
    discord_id = ctx.message.author.id
    db.execute('SELECT id,swarfarm FROM usernames WHERE id=?', (discord_id,))
    result = db.fetchone()

    if result is None:
        msg = "You haven't linked your Swarfarm account yet, use !set to do so."
        await ctx.send(msg)
    else:
        swarfarm_id = result[1]
        monster_fmt = ' '.join(monster).title()
        #path = '/home/pi/Documents/ruhbot/monsters/{}.json'.format(monster_fmt)
        path = 'C:\\Users\\Raffael\\Documents\\ruhBot\\monsters\\{}.json'.format(monster_fmt)

        if os.path.isfile(path):
            # load file
            with open(path) as data_file:
                data = json.load(data_file)

            monster_id = data['pk']
            stat_url = 'https://swarfarm.com/api/v2/profiles/{}/monsters/'.format(swarfarm_id)
            r1 = requests.get(stat_url, headers={'Accept': 'application/json',
                                        'Content-Type': 'application/json', })
            response = r1.json()
            result = ''
            for monster in response['results']:
                if monster['monster'] == monster_id:
                    instance_id = monster['id']

                    url2 = 'https://swarfarm.com/api/instance/{}'.format(instance_id)
                    r2 = requests.get(url2, headers={'Accept': 'application/json',
                                                'Content-Type': 'application/json', })
                    monster_info = r2.json()

                    if monster_info['monster']['is_awakened'] is True:
                        awaken_star = ':star:'
                    else:
                        awaken_star = ':star:'
                    stars = multiplyString(awaken_star, monster_info['stars'])
                    level = monster_info['level']
                    hp = monster_info['hp']
                    attack = monster_info['attack']
                    defense = monster_info['defense']
                    speed = monster_info['speed']
                    crit_rate = monster_info['crit_rate']
                    crit_damage = monster_info['crit_damage']
                    resistance = monster_info['resistance']
                    accuracy = monster_info['accuracy']

                    if not monster_info['runeinstance_set']:
                        final_sets = 'Missing Runes'
                        slots = '?/?/?'
                    else:
                        rune_sets = []
                        slot_two = ''
                        slot_four = ''
                        slot_six = ''
                        for rune in monster_info['runeinstance_set']:
                            rune_sets.append(rune['get_type_display'])
                        final_sets = checkRuneList(rune_sets)
                        for rune in monster_info['runeinstance_set']:
                            if rune['slot'] == 2:
                                slot_two = rune['get_main_stat_rune_display']
                            elif rune['slot'] == 4:
                                slot_four = rune['get_main_stat_rune_display']
                            elif rune['slot'] == 6:
                                slot_six = rune['get_main_stat_rune_display']
                        slot_list = []
                        for slot in [slot_two,slot_four,slot_six]:
                            slot_abbreviation = slot.replace('Accuracy', 'ACC').replace('CRI Dmg', 'CDMG').replace('CRI Rate', 'CR')
                            if slot_abbreviation == '':
                                slot_list.append('?')
                            else:
                                slot_list.append(slot_abbreviation)
                        slots = '{}'.format('/'.join(slot_list))

                    result = '{} {} Level {} - {} - {}\nHP: {} Attack: {} Def: {} SPD: {} CR: {}% CDMG: {}% Res: {}% Acc: {}% '.format(
                        monster_fmt, stars, level, final_sets, slots, hp, attack, defense, speed, crit_rate,
                        crit_damage, resistance, accuracy)
                    await ctx.send(result)

            if result == '':
                if monster_fmt[0] == 'A' or monster_fmt[0] == 'E' or monster_fmt[0] == 'O' or \
                                monster_fmt[0] == 'I' or monster_fmt[0] == 'U':
                    artikel = 'an'
                else:
                    artikel = 'a'
                await ctx.send("You don't have {} {}.".format(artikel, monster_fmt))
        else:
            await ctx.send('Monster not found.')

@bot.command(help='Returns all information about the specified skill of a monster.')
async def skill(ctx, skill: int, *monster: str):
    monster = ' '.join(monster).title()
    skill_nr = skill-1

    #path = '/home/pi/Documents/ruhbot/monsters/{}.json'.format(monster)
    path = 'C:\\Users\\Raffael\\Documents\\ruhBot\\monsters\\{}.json'.format(monster)

    if os.path.isfile(path):
        # load file
        with open(path) as data_file:
            data = json.load(data_file)

        # set variables
        skill_name = data['skills'][skill_nr]['name']
        if data['skills'][skill_nr]['cooltime'] is None:
            cooltime = 0
        else:
            cooltime = data['skills'][skill_nr]['cooltime']
        hits = data['skills'][skill_nr]['hits']
        skillups = data['skills'][skill_nr]['max_level']-1
        if skillups == 0:
            progress = '-'
        else:
            progress_raw = data['skills'][skill_nr]['level_progress_description']
            still_raw = progress_raw.replace('\r\n', ', ')
            if still_raw[-1] == '\n':
                progress = still_raw.replace('\n',', ')[:-2]
            else:
                progress = still_raw.replace('\n',', ')
        if data['skills'][skill_nr]['multiplier_formula_raw'] == '[]':
            multiplier = '-'
        else:
            mult = ast.literal_eval(data['skills'][skill_nr]['multiplier_formula_raw'])
            multiplier = ''
            for part in mult:
                if len(part) > 1:
                    piece = '({})'.format(' '.join(map(str, part)))
                else:
                    piece = ' '.join(map(str, part))
                multiplier += piece

            mult_dict = {'ATTACK_LOSS_HP': 'Lost HP', 'TARGET_TOT_HP': 'Enemy MAX HP',
                         'TARGET_CUR_HP_RATE': 'Enemy HP %', 'ATTACK_TOT_HP': 'MAX HP', 'ATTACK_SPEED': 'SPD',
                         'TARGET_SPEED': 'Enemy SPD'}

            for word in ['ATTACK_LOSS_HP','TARGET_TOT_HP','TARGET_CUR_HP_RATE','ATTACK_TOT_HP','ATTACK_SPEED','TARGET_SPEED']:
                multiplier = multiplier.replace(word,mult_dict[word])

        effect_list = []
        for effect in data['skills'][skill_nr]['skill_effect']:
            effect_list.append(effect['name'])
        effects = ' - '.join(effect_list)
        desc = data['skills'][skill_nr]['description']

        result = '**{0}**\n\nMultiplier: {7}, Hits: {2}, Skillups: {3}, Cooltime: {1}\nProgress: {4}\nEffects: {5}\n\nDescription: {6}'.format(
            skill_name, cooltime, hits, skillups, progress, effects, desc, multiplier)
    else:
        result = 'Monster not found.'

    await ctx.send(result)

@bot.command(help="Chooses one of the specified options. Use ' or ' as delimiter.")
async def choose(ctx):
    options = ctx.message.content[8:].split(' or ')
    choice = random.choice(options)
    await ctx.send(choice)

@bot.command(help="Chooses one of the specified options while showing the elimination process. Use ' or ' as delimiter.")
async def eliminate(ctx):
    options = ctx.message.content[11:].split(' or ')
    while (len(options) > 1):
        choice = random.choice(options)
        options.remove(choice)
        result = ' '.join(options)
        await ctx.send(result)

@bot.command(help="Returns the current top 5 Summoners War streams.")
async def streams(ctx):
    url = 'https://api.twitch.tv/kraken/streams/?game=Summoners%20War:%20Sky%20Arena&limit=5'
    r = requests.get(url, headers={'Client-ID': config.TWITCH_CLIENT_ID})
    response = r.json()
    streamers = []
    for stream in response['streams']:
        display_name = stream['channel']['display_name']
        name = stream['channel']['name']
        if name.lower() != display_name.lower():
            name_result = '{} ({})'.format(display_name, name)
        else:
            name_result = display_name
        viewers = stream['viewers']
        info = '* {} [{} Viewers]'.format(name_result, viewers)
        streamers.append(info)
    result = "```Markdown\n{}```".format('\n'.join(streamers))
    await ctx.send(result)

@bot.command(help="Uploads a preview image of the specified stream.")
async def preview(ctx, stream: str):
    url = 'https://api.twitch.tv/kraken/streams/{}'.format(stream)
    r = requests.get(url, headers={'Client-ID':config.TWITCH_CLIENT_ID})
    response = r.json()
    if response['stream'] is None:
        result = '{} is currently offline.'.format(stream)
        await ctx.send(result)
    else:
        preview = response['stream']['preview']['large']
        r2 = requests.get(preview)
        file = discord.File(BytesIO(r2.content), filename="preview.jpg")
        embed = discord.Embed()
        embed.set_image(url="attachment://preview.jpg")
        await ctx.send(file=file, embed=embed)

bot.run(config.DISCORD_TOKEN)