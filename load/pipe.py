import json
from urllib.parse import urlparse

from datetime import datetime
from dateutil.parser import parse as datetimeparser
from pathlib import Path
from collections import defaultdict

if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

from load.match import main as match

from json_model import TransformedArticles, HarvestExpanded


URLS = {
    urlparse('https://www.capito.senate.gov/news/press-releases').netloc: 11701,
    urlparse('https://www.booker.senate.gov/news/press').netloc: 76151,
    urlparse('https://aguilar.house.gov/category/congress_press_release/').netloc: 70114,
    urlparse('https://www.speaker.gov/news/').netloc: 28918,
    urlparse('https://www.baldwin.senate.gov/news/press-releases').netloc: 3470,
    urlparse('https://www.schatz.senate.gov/news/press-releases/').netloc: 17852,
    urlparse('https://www.ernst.senate.gov/news/press-releases').netloc: 128583,
    urlparse('https://www.schumer.senate.gov/newsroom/press-releases').netloc: 26976,
    urlparse('https://www.warren.senate.gov/newsroom/press-releases').netloc: 141272,
    urlparse('https://www.durbin.senate.gov/newsroom/press-releases').netloc: 26847,
    urlparse('https://www.cortezmasto.senate.gov/news/press-releases').netloc: 69579,
    urlparse('https://www.stabenow.senate.gov/news').netloc: 515,
    urlparse('https://www.manchin.senate.gov/newsroom/press-releases').netloc: 7547,
    urlparse('https://www.klobuchar.senate.gov/public/index.cfm/news-releases').netloc: 65092,
    urlparse('https://www.mcconnell.senate.gov/public/index.cfm/pressreleases').netloc: 53298,
    urlparse('https://www.thune.senate.gov/public/index.cfm/press-releases').netloc: 398,
    urlparse('https://www.barrasso.senate.gov/public/index.cfm/news-releases').netloc: 52662,
    urlparse('https://katherineclark.house.gov/press-releases').netloc: 35858,
    urlparse('https://stefanik.house.gov/media-center').netloc: 152539,
    urlparse('https://www.sanders.senate.gov/media/press-releases/').netloc: 27110,
    urlparse('https://www.murray.senate.gov/category/press-releases/').netloc: 53358,
    urlparse('https://www.daines.senate.gov/news/press-releases/').netloc: 135720,
    urlparse('https://www.majorityleader.gov/news/documentquery.aspx').netloc: 9026,
    urlparse('https://www.majoritywhip.gov/news/documentquery.aspx').netloc: 38894,
    urlparse('https://palmer.house.gov/media-center').netloc: 146274,
    urlparse('https://democraticleader.house.gov/media').netloc: 55285,
    urlparse('https://www.warner.senate.gov/public/index.cfm/pressreleases').netloc: 535,
    urlparse('https://clyburn.house.gov/press-releases').netloc: 27066,
}

#TODO: Revamp model so that a speech can be shared among candidates.
"""
HARVEST DATA MODEL:

Expanded
[ 
    {
    'candidate_id':...,
    'candidate_name': ...,
    'harvests' : [
        {   
            'metadata': {
                'title': ...,
                'speechdate': ...,
                'location': ...,
                'url': ...,
                },
            
            'content': [
                {
                    'speechtype_id:...,
                    'speechtext': ...,
                    'review': True | False,
                    'review_message': ...,
                },
                {
                    'speechtype_id:...,
                    'speechtext': ...,
                    'review': True | False,
                    'review_message': ...,
                },
                ...
                ]
        },
        ...
        ]
    },
    ...
]

Condensed
[
    {
    'candidate_id':...,
    'speechtype_id':...,
    'title':...,
    'speechdate':...,
    'location':...,
    'url':...,
    'speechtext':...,
    'review': True | False,
    'review_message': ...,
    },
    ...
]
"""

SPEECHTYPE = {
    1: 'Speech',
    2: 'Letter',
    3: 'Interview',
    4: 'Press Release',
    6: 'Statement',
    7: 'Issue Position',
    8: 'News Article',
    9: 'Op-Ed',
    10: 'Press Conference',
    11: 'Pledge',
    12: 'Debate',
    13: 'Hearing',
    14: 'Floor Speech',
    15: 'Social Media',
    16: 'Executive Order',
    17: 'Other'
}

SPEECH_MAP = {
    'statements': 4,
    'letters': 2,
    'speech': 1,
    'interview': 3,
}


# TODO: Candidate Aliases flag for review


def match_names_to_ids():
    pass


def main(transformed_json: TransformedArticles):
    name_ids = match(transformed_json)
    data = []

    for record in transformed_json.all:

        title = record.title
        speechdate = datetimeparser(record.timestamp).strftime('%Y-%m-%d')
        location = record.publish_location
        url = record.url
        exists = []

        for nlp_extract in record.statements.all:
            candidate_id_statements = defaultdict(dict)
            candidate_id_review = defaultdict(dict)
            speechtype_id = SPEECH_MAP.get(nlp_extract.name)
            speechtype = SPEECHTYPE.get(speechtype_id)

            # Check to see if it contains statements at all.
            for name in nlp_extract.attributed:
                match_info = name_ids[name]
                candidate_ids = match_info['candidate_id']
                match_status = match_info['match_status']

                if candidate_ids:
                    for candidate_id in candidate_ids:

                        if match_status == 'REVIEW':
                            candidate_id_review[candidate_id]['review'] = True
                            candidate_id_review[candidate_id]['review_message'] = "Candidate name may not be matched correctly"
                        elif match_status == 'AMBIGUOUS':
                            candidate_id_review[candidate_id]['review'] = True
                            candidate_id_review[candidate_id]['review_message'] = "Candidate names are matched ambiguously"
                        else:
                            candidate_id_review[candidate_id]['review'] = False
                            candidate_id_review[candidate_id]['review_message'] = None

                        for content in nlp_extract.contents.all:
                            content_text = content.text
                            for to_replace in content.to_replace.all:
                                content_text = content_text.replace(
                                    content.text[to_replace.start: to_replace.end], "")
                                
                            candidate_id_statements[candidate_id].update({content.start:content_text})

            if candidate_id_statements:
                exists.append(True)
            else:
                exists.append(False)

            for candidate_id, statements in candidate_id_statements.items():

                data.append(
                    {
                        'candidate_id': candidate_id,
                        'speechtype_id': speechtype_id,
                        'speechtype': speechtype,
                        'title': title,
                        'speechdate': speechdate,
                        'location': location,
                        'url': url,
                        'speechtext': '\n\n'.join(dict(sorted(statements.items())).values()),
                    }| candidate_id_review[candidate_id])

        if not any(exists):

            data.append(
                {
                    'candidate_id': URLS.get(urlparse(url).netloc),
                    'speechtype_id': 17,
                    'speechtype': SPEECHTYPE.get(17),
                    'title': title,
                    'speechdate': speechdate,
                    'location': location,
                    'url': url,
                    'speechtext': None,
                    'review': True,
                    'review_message': "Nothing is extracted from this article."
                })

    return HarvestExpanded(data)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(prog='ps_automation_load')
    parser.add_argument('filepath')

    args = parser.parse_args()

    working_dir = Path(args.filepath).parent.parent

    with open(Path(args.filepath), 'r') as f:
        transformed_json = TransformedArticles(json.load(f), as_root=True)

    harvest_json = main(transformed_json)
    harvest_json.save('harvest', working_dir/'HARVEST_FILES')
