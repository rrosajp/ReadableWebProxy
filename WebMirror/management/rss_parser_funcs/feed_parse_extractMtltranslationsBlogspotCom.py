def extractMtltranslationsBlogspotCom(item):
	'''
	Parser for 'mtltranslations.blogspot.com'
	'''

	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None

	tagmap = [
		('mr. ernest is my boyfriend',       'Mr. Earnest Is My Boyfriend',                      'translated'),
		('Once We Come Across Love',         'Once We Come Across Love',                         'translated'),
		('PRC',       'PRC',                      'translated'),
		('Loiterous', 'Loiterous',                'oel'),
	]

	for tagname, name, tl_type in tagmap:
		if tagname in item['tags']:
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)


	return False