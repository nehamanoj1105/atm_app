import json

n_json = '{"company":{"name":"Tech Innovations","departments":[{"name":"Engineering","teams":[{"name":"Backend Team","members":[{"name":"Alice","skills":["Java","Spring","Microservices"],"timestamp":"2023-10-01T10:00:00Z"},{"name":"Bob","skills":["Python","Django","Flask"],"timestamp":"2023-10-01T10:05:00Z"}]},{"name":"Frontend Team","members":[{"name":"Charlie","skills":["JavaScript","React","CSS"],"timestamp":"2023-10-01T10:10:00Z"},{"name":"Diana","skills":["HTML","Vue.js","Sass"],"timestamp":"2023-10-01T10:15:00Z"}]}]},{"name":"Marketing","campaigns":[{"name":"Product Launch","channels":[{"type":"Social Media","platforms":["Facebook","Instagram","Twitter"]},{"type":"Email","recipients":[{"name":"Customer List","emails":[["customer1@example.com","customer2@example.com"],["customer3@example.com","customer4@example.com"]]}]}]}]}]}}'

data = json.loads(n_json)

company = data['company']
name = company['name']
departments = company['departments'] 

print(name)
print(departments)
print(company)
print(data)
element_to_pop='name'
if element_to_pop in company:
    company.pop('name')

print(company)
