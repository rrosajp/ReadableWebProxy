def extractLangyascribeWordpressCom(item):
	'''
	Parser for 'langyascribe.wordpress.com'
	'''

	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None


	chp_prefixes = [
			('Chapter ',  'Lang Ya Bang',               'translated'),
		]
	
	
	if item['tags'] == ['Translated Chapters']:
		for prefix, series, tl_type in chp_prefixes:
			if item['title'].lower().startswith(prefix.lower()):
				return buildReleaseMessageWithType(item, series, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)



	return False