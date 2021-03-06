def extractWhatsawhizzerwebnovelsCom(item):
	'''
	Parser for 'whatsawhizzerwebnovels.com'
	'''

	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None
		
	
	badwords = [
			'isekai no monogatari',        # Comic
		]
	if any([bad in item['tags'] for bad in badwords]):
		return None


		
	if 'To unlock this content' in item['contents']:
		return None
	if 'This chapter can only be viewed' in item['contents']:
		return None
	if len(item['contents']) < 1000:
		return None
		
		
	# print(item['contents'])

	tagmap = [
		('Rise of the Midnight King',       'Rise of the Midnight King',                                                'oel'),
		('NTR Crush',                       'NTR Crush : I Will Steal Every Girl',                                      'oel'),
		('tales of a seductress',           'tales of a seductress',                                                    'oel'),
		('screwed by my boss',              'screwed by my boss',                                                       'oel'),
		('Hawtness',                        'Hawtness',                                                                 'oel'),
		('Time and Place',                  'The Timefall Saga - Time and Place',                                       'oel'),
		('EPASH',                           'Enslaved Pregnant Animalgirl Sister Harem With No NTR',                    'oel'),
		('Pushing Up Gravestones',          'Pushing Up Gravestones',                                                   'oel'),
		('My Dungeon Life',                 'My Dungeon Life',                                                          'oel'),
		('World of Women',                  'World of Women',                                                           'oel'),
		('getting lucky',                   'getting lucky',                                                            'oel'),
		('Tales of an Enchantress',         'Tales of an Enchantress',                                                  'oel'),
		('toae',                            'Tales of an Enchantress',                                                  'oel'),
		('moth',                            'The Man of the House',                                                     'oel'),
		('Power of Creation',               'Power of Creation',                                                        'oel'),
		('std',                             'Sex Trafficking for Dummies',                                              'oel'),
		('vampires kiss',                   'The Vampire’s Kiss',                                                       'oel'),
		('Requiem to the Stars',            'Requiem to the Stars',                                                     'oel'),
		('guy on a spaceship',              'Guy on a Spaceship',                                                       'oel'),
		('enslaved',                        'Enslaved Sister Harem',                                                    'oel'),
		('the last dread pirate',           'The Last Dread Pirate',                                                    'oel'),
		('zoo',                             'The Zoo',                                                                  'oel'),
		('apocalypse',                      'It’s Not Easy Making Money In the Apocalypse',                             'oel'),
		('Loiterous',                       'Loiterous',                                                                'oel'),
	]

	for tagname, name, tl_type in tagmap:
		if tagname in item['tags']:
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)

	chp_prefixes = [
			('My Dungeon Life – Chapter ',                                                   'My Dungeon Life',                                                          'oel'),
			('It’s Not Easy Making Money In the Apocalypse – Chapter ',                      'It’s Not Easy Making Money In the Apocalypse',                             'oel'),
			('Sex Trafficking for Dummies',                                                  'Sex Trafficking for Dummies',                                              'oel'),
		]

	for prefix, series, tl_type in chp_prefixes:
		if item['title'].lower().startswith(prefix.lower()):
			return buildReleaseMessageWithType(item, series, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)




	return False