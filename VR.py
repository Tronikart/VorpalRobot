import telegram
import random
import re

from uuid import uuid4
from telegram.ext import MessageHandler, Filters, Updater, InlineQueryHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, ParseMode

def roll(dice):
	limit = 1000
	endResult = {}
	endResult['error'] = False
	result = 0
	#################
	# It is a string
	#################
	if type(dice) == str:
		numberDice = int(dice.split('d')[0])
		endResult['diceAmount'] = numberDice
		modifier = 0 if len(dice.split('+')) < 2 else int(dice.split('+')[1])
		##############
		# Its xDy form
		###############
		if len(dice.split('d')) == 2:
			dieNumber = int(dice.split('d')[1]) if modifier == 0 else int(dice.split('+')[0].split('d')[1])
			endResult['faces'] = dieNumber
			###################
			# Only one die roll
			###################
			if numberDice == 1:
				endResult['multipleResult'] = False
				result = random.randrange(numberDice, dieNumber + 1)
				endResult['dice'] = str(result)
			###################
			# Several Die Roll
			###################
			else:
				endResult['multipleResult'] = True
				endResult['dice'] = ""
				# Avoiding negative numbers
				# i = numberDice if numberDice > 0 else -numberDice
				# i += 1
				i = 0
				result = 0
				# Going through all the dice rolls, at the end, delete the extra ' + ' and break
				if numberDice <= limit:
					numberDice = numberDice 
				else:
					endResult['error'] = True
					endResult['errorCode'] = 1
					return endResult
				while(True):
					if i < numberDice:
						aux = random.randrange(1, dieNumber + 1)
						result += aux
						if i == numberDice:
							pass
						else:
							endResult['dice'] += str(aux) + " + "
						i += 1
					else:
						endResult['dice'] = endResult['dice'][:len(endResult['dice'])-3]
						break
		##################
		# Its xDyDyDy form
		##################
		else:
			endResult['multipleResult'] = True
			dieNumber = int(dice.split('d')[1]) if modifier == 0 else int(dice.split('+')[0].split('d')[1])
			endResult['faces'] = dieNumber
			###################
			# Only one die roll
			###################
			if numberDice == 1:
				#endResult['multipleResult'] = True
				auxResult = random.randrange(numberDice, dieNumber + 1)
				#endResult['dice'] = str(auxResult)
			###################
			# Several Die Roll
			###################
			else:
				endResult['multipleResult'] = True
				endResult['dice'] = ""
				#i = numberDice if numberDice > 0 else -numberDice
				#i += 1
				i = 0
				auxResult = 0
				if numberDice <= limit:
					numberDice = numberDice
				else:
					endResult['error'] = True
					endResult['errorCode'] = 1
					return endResult
				while(True):
					if i < numberDice:
						i += 1
						aux = random.randrange(1, dieNumber + 1)
						auxResult += aux
					else:
						break
			# Recursively handling more than one dice roll
			recur = roll(str(auxResult) + dice[3:].split('+')[0])
			endResult['dice'] = ""
			if recur['error'] == False:
				result += recur['total']
				endResult['dice'] += recur['dice']
			else:
				endResult['error'] = True
		# Useful flags for printing info
		# Crit, fail, the dice that were added, if there was any error
		if result == dieNumber and numberDice == 1:
			endResult['crit'] = True 
		else:
			endResult['crit'] = False
		endResult['fail'] = True if result == 1 else False
		endResult['total'] = result + modifier
		endResult['dice'] = endResult['dice'] + " + (" + str(modifier) + ")" if modifier != 0 else endResult['dice']
	elif type(dice) == int:
		endResult['diceAmount'] = numberDice
		endResult['faces'] = dice
		modifier = 0
		endResult['total'] = random.randrange(1, dice+1)
		endResult['multipleResult'] = False
	else:
		endResult['error'] = True
		endResult['errorCode'] = 0
	
	if endResult['error']:
		pass
	else:
		endResult['multipleResult'] = True if modifier > 0 else endResult['multipleResult']
	return endResult


def treatRoll(dice):
	# Has flavor text following the roll
	if re.match(r'(\d+d\d+\s?\+?\s?\d?) ([a-zA-Z ]+$)', dice):
		hasOptions = False
		dice = re.findall(r'(\d+d\d+\s?\+?\s?\d?) ([a-zA-Z ]+$)', dice)
		damage = dice[0][1]
		dice = dice[0][0]
		rolledDice = roll(str(dice))
	# Has options along with the dice roll
	elif re.match(r'(\d+d\d+\s?\+?\s?\d?)([kl]+[0-9]+$)', dice):
		hasOptions = True
		dice = re.findall(r'(\d+d\d+\s?\+?\s?\d?)([kl]+[0-9]+$)', dice)
		damage = str()
		options = dice[0][1]
		dice = dice[0][0]
		rolledDice = roll(str(dice))
	# Regular roll
	else:
		hasOptions = False
		rolledDice = roll(str(dice))
		damage = str()
	Message = ""
	if rolledDice['error']:
		if rolledDice['errorCode'] == 0:
			Message += "Please input a valid syntax"
		elif rolledDice['errorCode'] == 1:
			Message = "Those were way too many dice, have 1d1 instead, hope the result helps as much as all those dice were going to.\n\n<b>Rolling: 1d1\nResult:</b> 1 <i>slow down damage </i>"
	else:
		if hasOptions:
			# Drop lowest
			if options.lower()[0] == "l":
				dropLimit = int(options[1:])
				output = str()
				total = int()
				dice = str(rolledDice['diceAmount']) + "d" +  str(rolledDice['faces']) + " and losing the lowest " + str(dropLimit)
				rollsInt = [int(x) for x in rolledDice['dice'].split('+')]
				rollsInt.sort()
				minRolls = rollsInt[:dropLimit]
				for num in [int(x) for x in rolledDice['dice'].split('+')]:
					if num in minRolls:
						output += '<i>' + str(num) + '</i>'
						minRolls.pop(minRolls.index(num))
					else:
						output += '<b>' + str(num) + '</b>'
						total += num
					output += ' + '
				rolls = str(output[:-3])
			# Keep highest
			elif options.lower()[0] == "k":
				keepLimit = int(options[1:])
				output = str()
				total = int()
				dice = str(rolledDice['diceAmount']) + "d" +  str(rolledDice['faces']) + " and keeping the highest " + str(keepLimit)
				rollsInt = [int(x) for x in rolledDice['dice'].split('+')]
				rollsInt.sort()
				rollsInt.reverse()
				maxRolls = rollsInt[:keepLimit]
				for num in [int(x) for x in rolledDice['dice'].split('+')]:
					if num in maxRolls:
						output += '<b>' + str(num) + '</b>'
						total += num
						maxRolls.pop(maxRolls.index(num))
					else:
						output += '<i>' + str(num) + '</i>'
					output += ' + '
				rolls = str(output[:-3])
			total = str(total)
		else:
			rolls = rolledDice['dice'].replace(str(rolledDice['faces']), "<b>" + str(rolledDice['faces']) + "</b>" )
			total = str(rolledDice['total'])
		if rolledDice['multipleResult']:
			Message += "<b>Rolling " + dice + ":\nRolls:</b> " + rolls + "\n<b>Total: </b>" + total + " <i>" +  damage + "</i>"
		else:
			Message += "<b>Rolling " + dice + ":\nResult: </b>" + total + " <i>" +  damage + "</i>"
		if rolledDice['crit'] and not rolledDice['fail']:
			Message += "\n<pre>CRIT!!</pre>"
		elif rolledDice['fail'] and not rolledDice['crit']:
			Message += "\n<pre>Critical Failure!</pre>"
		elif rolledDice['fail'] and rolledDice['crit']:
			Message += "\n<i>You rolled a d1, what did you expect?</i>"
	return Message

def handleQuery(query):
	if "k" in query.split(' ')[0]:
		number = query.split(' ')[0].split('k')[0]
		keep = query.split(' ')[0].split('k')[1]
		message = number + " keep the " + keep + " highest."
	elif 'l' in query.split(' ')[0]:
		number = query.split(' ')[0].split('l')[0]
		drop = query.split(' ')[0].split('l')[1]
		message = number + " drop the " + drop + " lowest."
	else:
		message = query
	return message

def inlineRoll(bot, update):
	query = update.inline_query.query
	helpMessage = "<b>Available roll combinations and options:</b>\n\n \
<b>Basic roll:</b> <code>[number]</code>d<code>[faces]</code>\n   <i>2d4</i>\n \
<b>Roll with modifier:</b> <code>[number]</code>d<code>[faces]</code>+<code>[modifier]</code>\n   <i>10d6 + -2</i> (can be positive or negative)\n \
<b>Roll with flavor text:</b> <code>[number]</code>d<code>[faces]</code> <code>[text]</code>\n   <i>1d10 fire damage</i> (can contain modifiers)\n \
<b>Roll and keep the highest:</b> <code>[number]</code>d<code>[faces]</code>k<code>[numberToKeep]</code>\n   <i>4d6k3</i>\n \
<b>Roll and lose the lowest:</b> <code>[number]</code>d<code>[faces]</code>l<code>[numberToDrop]</code>\n   <i>10d8d4</i>\n \
<b>Compound Roll:</b> <code>[number]</code>d<code>[faces]</code>d<code>[faces]</code>\n    <i>4d4d6d8</i>"

	if query:
		try:
			roll = treatRoll(query)
			if roll[0] == 'T':
				title = query + " are too many dice, will roll 1d1 instead."
				description = "Slow down, roll it separately if your REALLY need to roll this much dice."
			else:
				title = "Roll " + handleQuery(query)
				description = ""
			options = [InlineQueryResultArticle('result',
				title=title,
				thumb_url="https://i.imgur.com/ZjaMjNx.png",
				description = description,
				input_message_content=InputTextMessageContent(roll, parse_mode = "HTML"))]
		except:
			options = [InlineQueryResultArticle('result',
				title="Please input a valid format, click to roll a d20 either way.",
				thumb_url="https://i.imgur.com/Kw5Sjgf.png",
				input_message_content=InputTextMessageContent(treatRoll('1d20'), parse_mode = "HTML"))]
	else:
		options = [ 
			InlineQueryResultArticle(
				id=uuid4(), 
				title="Roll 1d20",
				description="Roll a 20 sided die.",
				thumb_url="https://i.imgur.com/Kw5Sjgf.png",
				input_message_content=InputTextMessageContent(treatRoll('1d20'), parse_mode = "HTML")),
			InlineQueryResultArticle(
				id=uuid4(),
				title="Roll 1d12",
				description="Roll a 12 sided die.",
				thumb_url="https://i.imgur.com/0ouwReP.png",
				input_message_content=InputTextMessageContent(treatRoll('1d12'), parse_mode = "HTML")),
			InlineQueryResultArticle(
				id=uuid4(),
				title="Roll 2d10",
				description="Roll two 10 sided die.",
				thumb_url="https://i.imgur.com/x1GcWWu.png",
				input_message_content=InputTextMessageContent(treatRoll('2d10'), parse_mode = "HTML")),
			InlineQueryResultArticle(
				id=uuid4(), 
				title="Roll 1d10",
				description="Roll a 10 sided die.",
				thumb_url="https://i.imgur.com/HCoFo5k.png",
				input_message_content=InputTextMessageContent(treatRoll('1d10'), parse_mode = "HTML")),
			InlineQueryResultArticle(
				id=uuid4(), 
				title="Roll 1d8",
				description="Roll a 8 sided die.",
				thumb_url="https://i.imgur.com/I5tYPv6.png",
				input_message_content=InputTextMessageContent(treatRoll('1d8'), parse_mode = "HTML")),
			InlineQueryResultArticle(
				id=uuid4(), 
				title="Roll 1d6",
				description="Roll a 6 sided die.",
				thumb_url="https://i.imgur.com/VXXCjQG.png",
				input_message_content=InputTextMessageContent(treatRoll('1d6'), parse_mode = "HTML")),
			InlineQueryResultArticle(
				id=uuid4(), 
				title="Roll 1d4",
				description="Roll a 4 sided die.",
				thumb_url="https://i.imgur.com/XqCLXOx.png",
				input_message_content=InputTextMessageContent(treatRoll('1d4'), parse_mode = "HTML")),
			InlineQueryResultArticle(
				id=uuid4(), 
				title="Help",
				thumb_url="https://i.imgur.com/ZjaMjNx.png",
				input_message_content=InputTextMessageContent(helpMessage, parse_mode = "HTML"))
			]

	update.inline_query.answer(options, cache_time=0)

def beep_bot(bot, update):
	CID = update.message.chat.id
    if update.message.text.lower() == "beep":
        bot.send_message(CID, "`Boop`", parse_mode="Markdown")
    else:
    	bot.send_message(CID, "`I only work through inline mode, write @VorpalRobot followed by a space to try it out.`", parse_mode="Markdown")



updater = Updater(token='TOKEN')
dispatcher = updater.dispatcher
dispatcher.add_handler(MessageHandler(Filters.text, beep_bot))
dispatcher.add_handler(InlineQueryHandler(inlineRoll))
updater.start_polling(clean=True)
print ("Running")
updater.idle()
