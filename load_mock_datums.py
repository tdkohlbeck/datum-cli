import subprocess

mock_data = [
    ['weight:150', 'coffee'],
    ['sleep:3/5', 'weight:152'],
    ['coffee'],
    ['sleep:4/5', 'coffee', 'weight:153'],
    ['coffee:2'],
]

for mock_datum in mock_data:
    subprocess.run(['datum', 'add'] + mock_datum)
