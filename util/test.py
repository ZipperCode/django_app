

def del_list(data_list):
    print("list = " + str(data_list))
    data_list.pop(0)
    print("list2 = " + str(data_list))

if __name__ == '__main__':
    _list = [1,2,3,4]
    del_list(_list)
    print("list3 = " + str(_list))