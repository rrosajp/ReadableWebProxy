def extractLetsgostargazingWordpressCom(item):
	'''
	Parser for 'letsgostargazing.wordpress.com'
	'''

	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None

	titlemap = [
		('MNLWYPBP chapter ',       'My new life, won’t you please become peaceful!',                      'translated'),
		('Loiterous', 'Loiterous',                'oel'),
	]

	for titlecomponent, name, tl_type in titlemap:
		if titlecomponent.lower() in item['title'].lower():
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)


	return False