# -*- coding: utf-8 -*-
import os

import crossplane
from crossplane.compat import basestring
from crossplane.builder import _enquote

here = os.path.dirname(__file__)


def assert_equal_payloads(a, b, ignore_keys=()):
    assert type(a) == type(b)
    if isinstance(a, list):
        assert len(a) == len(b)
        for args in zip(a, b):
            assert_equal_payloads(*args, ignore_keys=ignore_keys)
    elif isinstance(a, dict):
        keys = set(a.keys()) | set(b.keys())
        keys.difference_update(ignore_keys)
        for key in keys:
            assert_equal_payloads(a[key], b[key], ignore_keys=ignore_keys)
    elif isinstance(a, basestring):
        assert _enquote(a) == _enquote(b)
    else:
        assert a == b


def compare_parsed_and_built(conf_dirname, conf_basename, tmpdir, **kwargs):
    original_dirname = os.path.join(here, 'configs', conf_dirname)
    original_path = os.path.join(original_dirname, conf_basename)
    original_payload = crossplane.parse(original_path, **kwargs)
    original_parsed = original_payload['config'][0]['parsed']

    build1_config = crossplane.build(original_parsed)
    build1_file = tmpdir.join('build1.conf')
    build1_file.write(build1_config)
    build1_payload = crossplane.parse(build1_file.strpath, **kwargs)
    build1_parsed = build1_payload['config'][0]['parsed']

    assert_equal_payloads(original_parsed, build1_parsed, ignore_keys=['line'])

    build2_config = crossplane.build(build1_parsed)
    build2_file = tmpdir.join('build2.conf')
    build2_file.write(build2_config)
    build2_payload = crossplane.parse(build2_file.strpath, **kwargs)
    build2_parsed = build2_payload['config'][0]['parsed']

    assert build1_config == build2_config
    assert_equal_payloads(build1_parsed, build2_parsed, ignore_keys=[])


def test_build_nested_and_multiple_args():
    payload = [
        {
            "directive": "events",
            "args": [],
            "block": [
                {
                    "directive": "worker_connections",
                    "args": ["1024"]
                }
            ]
        },
        {
            "directive": "http",
            "args": [],
            "block": [
                {
                    "directive": "server",
                    "args": [],
                    "block": [
                        {
                            "directive": "listen",
                            "args": ["127.0.0.1:8080"]
                        },
                        {
                            "directive": "server_name",
                            "args": ["default_server"]
                        },
                        {
                            "directive": "location",
                            "args": ["/"],
                            "block": [
                                {
                                    "directive": "return",
                                    "args": ["200", "foo bar baz"]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]

    built = crossplane.build(payload, indent=4, tabs=False)

    assert built == '\n'.join([
        'events {',
        '    worker_connections 1024;',
        '}',
        'http {',
        '    server {',
        '        listen 127.0.0.1:8080;',
        '        server_name default_server;',
        '        location / {',
        "            return 200 'foo bar baz';",
        '        }',
        '    }',
        '}'
    ])

def test_build_with_comments():
    payload = [
        {
           "args" : [],
           "block" : [
              {
                 "args" : [
                    "1024"
                 ],
                 "line" : 2,
                 "directive" : "worker_connections"
              }
           ],
           "line" : 1,
           "directive" : "events"
        },
        {
           "directive" : "#",
           "line" : 4,
           "comment" : "comment",
           "args" : []
        },
        {
           "directive" : "http",
           "block" : [
              {
                 "args" : [],
                 "line" : 6,
                 "block" : [
                    {
                       "args" : [
                          "127.0.0.1:8080"
                       ],
                       "line" : 7,
                       "directive" : "listen"
                    },
                    {
                       "directive" : "#",
                       "line" : 7,
                       "comment" : "listen",
                       "args" : []
                    },
                    {
                       "args" : [
                          "default_server"
                       ],
                       "directive" : "server_name",
                       "line" : 8
                    },
                    {
                       "args" : [
                          "/"
                       ],
                       "directive" : "location",
                       "line" : 9,
                       "block" : [
                          {
                             "args" : [],
                             "directive" : "#",
                             "line" : 9,
                             "comment" : "# this is brace"
                          },
                          {
                             "directive" : "#",
                             "comment" : " location /",
                             "line" : 10,
                             "args" : []
                          },
                          {
                             "directive" : "#",
                             "comment" : " is here",
                             "line" : 11,
                             "args" : []
                          },
                          {
                             "args" : [
                                "200",
                                "foo bar baz"
                             ],
                             "line" : 11,
                             "directive" : "return"
                          }
                       ]
                    }
                 ],
                 "directive" : "server"
              }
           ],
           "line" : 5,
           "args" : []
        }
     ]

    built = crossplane.build(payload, indent=4, tabs=False)

    assert built == '\n'.join([
        'events {',
        '    worker_connections 1024;',
        '}',
        '#comment',
        'http {',
        '    server {',
        '        listen 127.0.0.1:8080; #listen',
        '        server_name default_server;',
        '        location / { ## this is brace',
        '            # location /',
        '            # is here',
        "            return 200 'foo bar baz';",
        '        }',
        '    }',
        '}'
    ])

def test_compare_parsed_and_built_simple(tmpdir):
    compare_parsed_and_built('simple', 'nginx.conf', tmpdir)


def test_compare_parsed_and_built_messy(tmpdir):
    compare_parsed_and_built('messy', 'nginx.conf', tmpdir)


def test_compare_parsed_and_built_messy_with_comments(tmpdir):
    compare_parsed_and_built('with-comments', 'nginx.conf', tmpdir, comments=True)