def extractGrasstranslatesBlogspotCom(item):
	'''
	Parser for 'grasstranslates.blogspot.com'
	'''

	vol, chp, frag, postfix = extractVolChapterFragmentPostfix(item['title'])
	if not (chp or vol) or "preview" in item['title'].lower():
		return None

	tagmap = [
		('PGS',       'Peerless Genius System',                         'translated'),
		('dkfod',     'Devil King from the Otherworldly Dimension',     'translated'),
		('fls',       'Full-time Lottery System',                      'translated'),
		('PRC',       'PRC',                      'translated'),
		('Loiterous', 'Loiterous',                'oel'),
	]

	for tagname, name, tl_type in tagmap:
		if tagname in item['tags']:
			return buildReleaseMessageWithType(item, name, vol, chp, frag=frag, postfix=postfix, tl_type=tl_type)


	return False