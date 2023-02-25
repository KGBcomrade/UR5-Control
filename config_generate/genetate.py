# params

id = 949

'''
Параметры для перевода координат расположения сенсора из единиц шага решетки отверстий в столе в миллиметры в системе отсчета робота.
Смотреть на стенд нужно со стороны короткой части стола == со стороны, где вторая команда сидит. 
'''
xn = 5  ## вертикальная ось, положительное навправление вниз
yn = 1  ## горизнотальная ось, положительное направление вправо
## задается как номер дырочки (нумерация с нуля)




step = 25   # расстояние между дырками = шаг решетки (мм)
outfile = open(f"{id}.yaml", 'w')
templ_file = open("config_generate/template.yaml", 'r')

replace_patterns = [["$id", str(id)], 
                    ["$luc", f"[{454 + step*(xn-1)}, {-307.7 + step*(yn-1)}]"], 
                    ["$rdc", f"[{472 + step*(xn-1)}, {-268.7 + step*(yn-1)}]"]]

for line in templ_file:
    for pattern in replace_patterns:
        line = line.replace(*pattern)
    outfile.write(line)
    # print(line, end="")
    