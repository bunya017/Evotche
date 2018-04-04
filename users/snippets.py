import random



def gen_token(number, length):
	pop = 'QWERTYUIOPLKJHGFDSAZXCVBNMmnbvcxzasdfghjklpoiuytrewq0987654321'
	token = []
	for i in range(number):
		token.append(''.join(random.sample(pop, length)))
	return token