import openpyxl
import pandas as pd
import pickle


def within_range(bounds: tuple, cell: openpyxl.cell) -> bool:
    """
    Функция, определяющая, входит ли клетка в состав большой слитой или нет.
    :param bounds: границы merged клеток
    :param cell: сама клетка
    :return: True, если merged клетка, иначе False
    """
    column_start, row_start, column_end, row_end = bounds  # границы merged клетки
    row = cell.row  # проверка, находится ли клетка в этом слиянии
    if row_start <= row <= row_end:  #              ___________________
        column = cell.column  #                     |value|empty|empty|
        if column_start <= column <= column_end:  # |empty|empty|empty|  Пример merged клетки
            return True  #                          |empty|empty|empty|
    return False  #


def get_value_merged(sheet: openpyxl.worksheet, cell: openpyxl.cell) -> any:
    """
    Функция, возвращающая значение, лежащее в клетке, вне зависимости от того, является ли клетка merged, или нет.
    :param sheet: таблица с расписанием
    :param cell: клетка таблицы
    :return: значение, лежащее в клетке
    """
    for merged in sheet.merged_cells:  # смотрим в списке слитых клеток (структура данных openpyxl.worksheet)
        if within_range(merged.bounds, cell):
            return sheet.cell(merged.min_row, merged.min_col).value
    return cell.value


def get_timetable(table: openpyxl.worksheet) -> dict:
    """
    Функция, которая из таблицы Excel с расписанием выделяет расписание для каждой группы.
    :param table: таблица с расписанием
    :return: Словарь, ключи в котором являются номерами групп, а
    значение, соответствующее ключу - расписание для этой группы.
    """
    groups = {}  # список расписаний для групп

    for j in range(3, table.max_column + 1):  # смотрим на значения по столбцам
        name = table.cell(1, j).value  # номер группы
        if name in ['Дни', 'Часы']:  # если это не номер группы, то пропускаем столбец
            continue
        # иначе если столбец - это номер группы, то составляем для него расписание
        elif name is not None:
            if type(name) == int:  # если номер группы - просто число, преобразуем его в строку
                name = str(name)
            # group - словарь с расписанием для группы
            group = dict(Понедельник={}, Вторник={}, Среда={}, Четверг={}, Пятница={}, Суббота={}, Воскресенье={})
            for k in range(2, table.max_row + 1):  # проходимся по столбцу
                # если клетки относятся ко дню недели (не разделители)
                if get_value_merged(table, table.cell(k, 1)) in group.keys():
                    day = get_value_merged(table, table.cell(k, 1))  # значение дня недели
                    time = get_value_merged(table, table.cell(k, 2))  # клетка, в которой лежит значение времени
                    pair = get_value_merged(table, table.cell(k, j))  # клетка, в которой лежит значение пары

                    # рассматриваем только те клетки, для которых определено значение как пары, так и времени
                    if (time, pair) != (None, None):
                        time = time.split()  # преобразуем время пары к формату hh:mm – hh:mm
                        if len(time[0][:-2]) == 1:
                            time[0] = '0' + time[0]
                        time = time[0][:-2] + ':' + time[0][-2:] + ' – ' + time[2][:-2] + ':' + time[2][-2:]
                        group[day][time] = pair  # записываем значение в расписание

            group = pd.DataFrame(group)  # заменяем None на спящие смайлики
            group.replace(to_replace=[None], value='😴', inplace=True)
            groups[name] = group  # заносим расписание для группы в словарь

    return groups  # словарь с группами


def timetable_by_group(course: int, group: str, day: str) -> pd.DataFrame:
    """
    Функция, выдающая расписание для нужной группы на требуемый день.
    :param course: номер курса
    :param group: номер группы
    :param day: день недели, расписание на который нужно вызвать
    :return: расписание в формате pd.DataFrame()
    """
    # датафреймы с расписаниями для каждого курса хранятся в файлах формата .pickle
    with open('timetable/{}_kurs.pickle'.format(course), 'rb') as handle:
        curr_groups = pickle.load(handle)
    # если номер группы есть в списке, то выдаем нужное расписание
    if group in curr_groups.keys() and day in ['Понедельник', 'Вторник', 'Среда',
                                               'Четверг', 'Пятница', 'Суббота', 'Воскресенье']:
        return curr_groups[group][day].to_frame()
    else:  # иначе выдаем пустой датафрейм
        return pd.DataFrame()


def check_group(group_num: str, course_num: int) -> bool:
    """
    Функция, которая проверяет наличие группы в списке групп по номеру курса.
    :param group_num: номер группы
    :param course_num: номер курса
    :return: True or False
    """
    flag = False
    with open('timetable/{}_kurs.pickle'.format(course_num), 'rb') as handle:
        curr_groups = pickle.load(handle)
    if group_num in curr_groups.keys():
        flag = True
    return flag
