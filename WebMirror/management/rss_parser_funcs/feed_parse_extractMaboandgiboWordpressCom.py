def extractMaboandgiboWordpressCom(item):
	'''
	Parser for 'maboandgibo.wordpress.com'
	'''
	
	if 'Indonesian' in item['tags']:
		return None

	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None

	tagmap = [
		('Shinka no Mi', 'Shinka no Mi',                'translated'),
		('Loiterous', 'Loiterous',                'oel'),
	]

	for tagname, name, tl_type in tagmap:
		if tagname in item['tags']:
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)


	return False