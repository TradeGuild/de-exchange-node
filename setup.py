from setuptools import setup

classifiers = [
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 2",
    "Topic :: Software Development :: Libraries",
]

setup(
    name='De Exchange Node',
    version='0.0.2',
    description='Each Exchange Node operates a single orderbook, representing a currency pair (i.e. BTC/USD). With REST API.',
    author='Deginner',
    author_email='support@deginner.com',
    url='https://github.com/deginner/de-exchange-node',
    license='MIT',
    classifiers=classifiers,
    packages=['dex_node'],
    package_data={'dex_node': ['static/*.json']},
    setup_requires=['pytest-runner'],
    install_requires=[
        "secp256k1==0.11",
        "bitjws==0.6.3.1",
        "mq_client >= 0.0.2",
        "amqp",
        "pika",
        "redis",
        'sqlalchemy>=1.0.9',
        "jsonschema",
        "alchemyjsonschema",
        "flask>=0.10.0",
        "Flask-login",
        "Flask-cors",
        "flask-bitjws>=0.1.1.4"
    ],
    tests_require=[
        "pytest",
        "pytest-cov"
    ]
)
