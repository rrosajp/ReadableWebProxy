def extractTranslationsdrtWordpressCom(item):
	'''
	Parser for 'translationsdrt.wordpress.com'
	'''

	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None

	tagmap = [
		('iceblade magician',       'The Iceblade Magician Rules over the World',                      'translated'),
		('wortenia',                'Wortenia Senki',                                                  'translated'),
		('Wortenia Senki',          'Wortenia Senki',                                                  'translated'),
		('PRC',       'PRC',                      'translated'),
		('Loiterous', 'Loiterous',                'oel'),
	]

	for tagname, name, tl_type in tagmap:
		if tagname in item['tags']:
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)


	return False