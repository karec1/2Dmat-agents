import matplotlib
matplotlib.use('Agg')  # Для использования без GUI
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import base64
from io import BytesIO
import ase
from ase import Atoms
from ase.io import read, write
from ase.visualize.plot import plot_atoms
import matplotlib.patches as mpatches

class StructureVisualizer:
    """Класс для визуализации кристаллических структур"""
    
    @staticmethod
    def create_structure_plot(cif_path, output_path=None, dpi=150):
        """
        Создает 2D изображение кристаллической структуры из CIF файла
        """
        try:
            atoms = read(cif_path)
            
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection='3d')
            
            # Получаем позиции атомов
            positions = atoms.get_positions()
            symbols = atoms.get_chemical_symbols()
            numbers = atoms.get_atomic_numbers()
            
            # Цвета для разных элементов
            element_colors = {
                1: 'gray',    # H
                6: 'black',   # C
                7: 'blue',    # N
                8: 'red',     # O
                14: 'orange', # Si
                26: 'brown',  # Fe
                24: 'green',  # Cr
                42: 'cyan',   # Mo
                74: 'purple', # W
                53: 'pink',   # I
            }
            
            # Размеры атомов
            atomic_radii = {
                1: 0.3,   # H
                6: 0.7,   # C
                7: 0.65,  # N
                8: 0.6,   # O
                14: 1.1,  # Si
                26: 1.4,  # Fe
                24: 1.3,  # Cr
                42: 1.3,  # Mo
                74: 1.3,  # W
                53: 1.4,  # I
            }
            
            # Рисуем атомы
            for pos, num in zip(positions, numbers):
                color = element_colors.get(num, 'gray')
                radius = atomic_radii.get(num, 0.7)
                
                # Сфера
                u = np.linspace(0, 2 * np.pi, 30)
                v = np.linspace(0, np.pi, 30)
                x = radius * np.outer(np.cos(u), np.sin(v)) + pos[0]
                y = radius * np.outer(np.sin(u), np.sin(v)) + pos[1]
                z = radius * np.outer(np.ones(np.size(u)), np.cos(v)) + pos[2]
                
                ax.plot_surface(x, y, z, color=color, alpha=0.8)
            
            # Рисуем связи
            if len(atoms) > 1:
                from ase.neighborlist import NeighborList
                nl = NeighborList([2.0] * len(atoms), self_interaction=False, 
                                 bothways=True)
                nl.update(atoms)
                
                for i in range(len(atoms)):
                    indices, offsets = nl.get_neighbors(i)
                    for j, offset in zip(indices, offsets):
                        pos_i = atoms.positions[i]
                        pos_j = atoms.positions[j] + np.dot(offset, atoms.get_cell())
                        
                        # Рисуем линию между атомами
                        ax.plot([pos_i[0], pos_j[0]],
                                [pos_i[1], pos_j[1]],
                                [pos_i[2], pos_j[2]],
                                'k-', linewidth=1, alpha=0.5)
            
            # Настройки осей
            ax.set_xlabel('X (Å)', fontsize=12)
            ax.set_ylabel('Y (Å)', fontsize=12)
            ax.set_zlabel('Z (Å)', fontsize=12)
            ax.set_title(f'Кристаллическая структура: {atoms.get_chemical_formula()}', 
                        fontsize=14, pad=20)
            
            # Легенда для элементов
            unique_elements = set(symbols)
            legend_patches = []
            for elem in unique_elements:
                for num, sym in element_colors.items():
                    if ase.data.chemical_symbols[num] == elem:
                        patch = mpatches.Patch(color=sym, label=elem)
                        legend_patches.append(patch)
                        break
            
            if legend_patches:
                ax.legend(handles=legend_patches, loc='upper right')
            
            plt.tight_layout()
            
            if output_path:
                plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
                plt.close()
                return output_path
            else:
                # Возвращаем изображение как base64
                buf = BytesIO()
                plt.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
                plt.close()
                buf.seek(0)
                img_str = base64.b64encode(buf.read()).decode('utf-8')
                return f"data:image/png;base64,{img_str}"
                
        except Exception as e:
            print(f"Ошибка визуализации структуры: {e}")
            return None
    
    @staticmethod
    def create_reciprocal_lattice_plot(cif_path, output_path=None):
        """
        Создает визуализацию обратной решетки
        """
        try:
            atoms = read(cif_path)
            
            # Получаем обратную решетку
            cell = atoms.get_cell()
            reciprocal_cell = cell.reciprocal()
            
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection='3d')
            
            # Векторы обратной решетки
            vectors = reciprocal_cell
            origin = np.zeros(3)
            
            # Цвета для векторов
            colors = ['r', 'g', 'b']
            labels = ['b₁', 'b₂', 'b₃']
            
            for i in range(3):
                ax.quiver(*origin, *vectors[i], 
                         color=colors[i], label=labels[i],
                         arrow_length_ratio=0.1, linewidth=2)
            
            # Рисуем точки обратной решетки
            n_points = 3
            points = []
            
            for i in range(-n_points, n_points+1):
                for j in range(-n_points, n_points+1):
                    for k in range(-n_points, n_points+1):
                        point = i * vectors[0] + j * vectors[1] + k * vectors[2]
                        points.append(point)
            
            points = np.array(points)
            ax.scatter(points[:, 0], points[:, 1], points[:, 2], 
                      c='black', s=20, alpha=0.6)
            
            # Первая зона Бриллюэна (упрощенная)
            # Для кубических/гексагональных систем
            if atoms.cell.cellpar()[3:] == (90, 90, 90):
                # Простая кубическая
                pass
            
            ax.set_xlabel('b₁ (Å⁻¹)', fontsize=12)
            ax.set_ylabel('b₂ (Å⁻¹)', fontsize=12)
            ax.set_zlabel('b₃ (Å⁻¹)', fontsize=12)
            ax.set_title('Обратная решетка', fontsize=14, pad=20)
            ax.legend()
            
            plt.tight_layout()
            
            if output_path:
                plt.savefig(output_path, dpi=150, bbox_inches='tight')
                plt.close()
                return output_path
            else:
                buf = BytesIO()
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                plt.close()
                buf.seek(0)
                img_str = base64.b64encode(buf.read()).decode('utf-8')
                return f"data:image/png;base64,{img_str}"
                
        except Exception as e:
            print(f"Ошибка визуализации обратной решетки: {e}")
            return None
    
    @staticmethod
    def create_interactive_structure(cif_path):
        """
        Создает интерактивную 3D визуализацию с помощью plotly
        """
        try:
            atoms = read(cif_path)
            
            # Получаем данные атомов
            positions = atoms.get_positions()
            symbols = atoms.get_chemical_symbols()
            
            # Создаем trace для атомов
            traces = []
            
            # Разные цвета для разных элементов
            element_colors = {
                'H': 'gray', 'C': 'black', 'N': 'blue', 'O': 'red',
                'Si': 'orange', 'Fe': 'brown', 'Cr': 'green',
                'Mo': 'cyan', 'W': 'purple', 'I': 'pink'
            }
            
            # Разные символы для 3D точечной диаграммы
            element_symbols = {
                'H': 'circle', 'C': 'circle', 'N': 'square', 'O': 'diamond',
                'Si': 'cross', 'Fe': 'x', 'Cr': 'triangle-up',
                'Mo': 'triangle-down', 'W': 'star', 'I': 'hexagram'
            }
            
            # Группируем атомы по элементам
            elements = {}
            for i, (pos, sym) in enumerate(zip(positions, symbols)):
                if sym not in elements:
                    elements[sym] = {'x': [], 'y': [], 'z': [], 'indices': []}
                elements[sym]['x'].append(pos[0])
                elements[sym]['y'].append(pos[1])
                elements[sym]['z'].append(pos[2])
                elements[sym]['indices'].append(i)
            
            # Создаем trace для каждого элемента
            for sym, data in elements.items():
                color = element_colors.get(sym, 'gray')
                marker_symbol = element_symbols.get(sym, 'circle')
                
                trace = go.Scatter3d(
                    x=data['x'],
                    y=data['y'],
                    z=data['z'],
                    mode='markers',
                    name=sym,
                    marker=dict(
                        size=8,
                        color=color,
                        symbol=marker_symbol,
                        line=dict(width=0.5, color='darkgray')
                    ),
                    text=[f'Atom {i+1}: {sym}' for i in data['indices']],
                    hoverinfo='text'
                )
                traces.append(trace)
            
            # Рисуем связи
            if len(atoms) > 1:
                from ase.neighborlist import NeighborList
                nl = NeighborList([2.0] * len(atoms), self_interaction=False, 
                                 bothways=True)
                nl.update(atoms)
                
                bond_lines = {'x': [], 'y': [], 'z': []}
                
                for i in range(len(atoms)):
                    indices, offsets = nl.get_neighbors(i)
                    for j, offset in zip(indices, offsets):
                        if i < j:  # Чтобы не рисовать связь дважды
                            pos_i = atoms.positions[i]
                            pos_j = atoms.positions[j] + np.dot(offset, atoms.get_cell())
                            
                            bond_lines['x'].extend([pos_i[0], pos_j[0], None])
                            bond_lines['y'].extend([pos_i[1], pos_j[1], None])
                            bond_lines['z'].extend([pos_i[2], pos_j[2], None])
                
                if bond_lines['x']:
                    bond_trace = go.Scatter3d(
                        x=bond_lines['x'],
                        y=bond_lines['y'],
                        z=bond_lines['z'],
                        mode='lines',
                        name='Bonds',
                        line=dict(color='gray', width=2),
                        hoverinfo='none',
                        showlegend=True
                    )
                    traces.append(bond_trace)
            
            # Создаем layout
            layout = go.Layout(
                title=f'3D структура: {atoms.get_chemical_formula()}',
                scene=dict(
                    xaxis=dict(title='X (Å)'),
                    yaxis=dict(title='Y (Å)'),
                    zaxis=dict(title='Z (Å)'),
                    aspectmode='data'
                ),
                margin=dict(l=0, r=0, b=0, t=40),
                showlegend=True,
                legend=dict(x=1.02, y=1)
            )
            
            fig = go.Figure(data=traces, layout=layout)
            
            # Конвертируем в HTML
            html_str = fig.to_html(full_html=False, include_plotlyjs='cdn')
            return html_str
            
        except Exception as e:
            print(f"Ошибка создания интерактивной визуализации: {e}")
            return None


class BandStructureVisualizer:
    """Класс для визуализации зонной структуры"""
    
    @staticmethod
    def create_band_structure_plot(data, output_path=None):
        """
        Создает график зонной структуры из данных
        data: словарь с ключами 'kpoints', 'energies', 'labels'
        """
        try:
            kpoints = np.array(data.get('kpoints', []))
            energies = np.array(data.get('energies', []))
            labels = data.get('labels', {})
            
            if len(kpoints) == 0 or len(energies) == 0:
                return None
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Рисуем зоны
            if energies.ndim == 2:
                for band in energies.T:
                    ax.plot(kpoints, band, 'b-', linewidth=1, alpha=0.7)
            else:
                ax.plot(kpoints, energies, 'b-', linewidth=1, alpha=0.7)
            
            # Линия Ферми
            ax.axhline(y=0, color='r', linestyle='--', linewidth=1, alpha=0.7)
            
            # Настройка осей
            ax.set_xlabel('Волновой вектор', fontsize=14)
            ax.set_ylabel('Энергия (эВ)', fontsize=14)
            ax.set_title('Зонная структура', fontsize=16, pad=20)
            
            # Метки высокосимметричных точек
            if labels:
                tick_positions = []
                tick_labels = []
                
                for label, position in labels.items():
                    if position in kpoints:
                        idx = np.where(kpoints == position)[0][0]
                        tick_positions.append(position)
                        tick_labels.append(f'${label}$')
                
                ax.set_xticks(tick_positions)
                ax.set_xticklabels(tick_labels, fontsize=12)
                
                # Вертикальные линии в высокосимметричных точках
                for pos in tick_positions:
                    ax.axvline(x=pos, color='gray', linestyle=':', linewidth=0.5)
            
            # Сетка
            ax.grid(True, alpha=0.3)
            
            # Легенда
            ax.legend(['Зоны', 'Уровень Ферми'], loc='upper right')
            
            plt.tight_layout()
            
            if output_path:
                plt.savefig(output_path, dpi=150, bbox_inches='tight')
                plt.close()
                return output_path
            else:
                buf = BytesIO()
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                plt.close()
                buf.seek(0)
                img_str = base64.b64encode(buf.read()).decode('utf-8')
                return f"data:image/png;base64,{img_str}"
                
        except Exception as e:
            print(f"Ошибка визуализации зонной структуры: {e}")
            return None
    
    @staticmethod
    def create_interactive_bands(data):
        """
        Создает интерактивный график зонной структуры
        """
        try:
            kpoints = np.array(data.get('kpoints', []))
            energies = np.array(data.get('energies', []))
            labels = data.get('labels', {})
            
            fig = go.Figure()
            
            # Рисуем зоны
            if energies.ndim == 2:
                for i in range(energies.shape[1]):
                    fig.add_trace(go.Scatter(
                        x=kpoints,
                        y=energies[:, i],
                        mode='lines',
                        name=f'Зона {i+1}',
                        line=dict(color='blue', width=1),
                        opacity=0.7,
                        showlegend=False
                    ))
            else:
                fig.add_trace(go.Scatter(
                    x=kpoints,
                    y=energies,
                    mode='lines',
                    name='Зоны',
                    line=dict(color='blue', width=1),
                    opacity=0.7
                ))
            
            # Линия Ферми
            fig.add_hline(y=0, line=dict(color='red', dash='dash', width=1))
            
            # Настройка осей
            fig.update_layout(
                title='Зонная структура',
                xaxis=dict(
                    title='Волновой вектор',
                    tickmode='array',
                    tickvals=[],
                    ticktext=[]
                ),
                yaxis=dict(title='Энергия (эВ)'),
                showlegend=True,
                hovermode='x unified'
            )
            
            # Метки высокосимметричных точек
            if labels:
                tick_positions = []
                tick_labels = []
                
                for label, position in labels.items():
                    if position in kpoints:
                        tick_positions.append(position)
                        tick_labels.append(f'{label}')
                
                fig.update_xaxis(
                    tickmode='array',
                    tickvals=tick_positions,
                    ticktext=tick_labels
                )
            
            # Конвертируем в HTML
            html_str = fig.to_html(full_html=False, include_plotlyjs='cdn')
            return html_str
            
        except Exception as e:
            print(f"Ошибка создания интерактивной зонной структуры: {e}")
            return None


class DOSVisualizer:
    """Класс для визуализации плотности состояний"""
    
    @staticmethod
    def create_dos_plot(data, output_path=None):
        """
        Создает график плотности состояний
        data: словарь с ключами 'energy', 'total_dos', 'partial_dos'
        """
        try:
            energy = np.array(data.get('energy', []))
            total_dos = np.array(data.get('total_dos', []))
            partial_dos = data.get('partial_dos', {})
            
            if len(energy) == 0 or len(total_dos) == 0:
                return None
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # Общая DOS
            ax1.plot(total_dos, energy, 'b-', linewidth=2)
            ax1.axhline(y=0, color='r', linestyle='--', linewidth=1)
            ax1.fill_betweenx(energy, 0, total_dos, where=(total_dos > 0), 
                             alpha=0.3, color='blue')
            ax1.set_xlabel('Плотность состояний', fontsize=12)
            ax1.set_ylabel('Энергия (эВ)', fontsize=12)
            ax1.set_title('Общая плотность состояний', fontsize=14)
            ax1.grid(True, alpha=0.3)
            
            # Частичная DOS (если есть)
            if partial_dos:
                colors = plt.cm.tab10(np.linspace(0, 1, len(partial_dos)))
                
                for i, (orbital, dos_data) in enumerate(partial_dos.items()):
                    dos_values = np.array(dos_data)
                    ax2.plot(dos_values, energy, label=orbital, 
                            color=colors[i], linewidth=2)
                    ax2.fill_betweenx(energy, 0, dos_values, 
                                     where=(dos_values > 0), 
                                     alpha=0.3, color=colors[i])
                
                ax2.axhline(y=0, color='r', linestyle='--', linewidth=1)
                ax2.set_xlabel('Плотность состояний', fontsize=12)
                ax2.set_ylabel('Энергия (эВ)', fontsize=12)
                ax2.set_title('Частичная плотность состояний', fontsize=14)
                ax2.legend(loc='best')
                ax2.grid(True, alpha=0.3)
            else:
                ax2.remove()
            
            plt.suptitle('Плотность состояний', fontsize=16, y=1.02)
            plt.tight_layout()
            
            if output_path:
                plt.savefig(output_path, dpi=150, bbox_inches='tight')
                plt.close()
                return output_path
            else:
                buf = BytesIO()
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                plt.close()
                buf.seek(0)
                img_str = base64.b64encode(buf.read()).decode('utf-8')
                return f"data:image/png;base64,{img_str}"
                
        except Exception as e:
            print(f"Ошибка визуализации DOS: {e}")
            return None
    
    @staticmethod
    def create_interactive_dos(data):
        """
        Создает интерактивный график DOS
        """
        try:
            energy = np.array(data.get('energy', []))
            total_dos = np.array(data.get('total_dos', []))
            partial_dos = data.get('partial_dos', {})
            
            fig = go.Figure()
            
            # Общая DOS
            fig.add_trace(go.Scatter(
                x=total_dos,
                y=energy,
                mode='lines',
                name='Total DOS',
                line=dict(color='blue', width=2),
                fill='tozerox',
                fillcolor='rgba(0, 0, 255, 0.3)'
            ))
            
            # Частичная DOS
            if partial_dos:
                colors = ['red', 'green', 'orange', 'purple', 'brown']
                
                for i, (orbital, dos_data) in enumerate(partial_dos.items()):
                    if i < len(colors):
                        color = colors[i]
                    else:
                        color = 'gray'
                    
                    dos_values = np.array(dos_data)
                    fig.add_trace(go.Scatter(
                        x=dos_values,
                        y=energy,
                        mode='lines',
                        name=f'{orbital}',
                        line=dict(color=color, width=2),
                        fill='tozerox',
                        fillcolor=f'rgba{tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (0.3,)}'
                    ))
            
            # Линия Ферми
            fig.add_hline(y=0, line=dict(color='red', dash='dash', width=1))
            
            fig.update_layout(
                title='Плотность состояний',
                xaxis=dict(title='Плотность состояний'),
                yaxis=dict(title='Энергия (эВ)'),
                showlegend=True,
                hovermode='y unified',
                legend=dict(x=1.02, y=1)
            )
            
            html_str = fig.to_html(full_html=False, include_plotlyjs='cdn')
            return html_str
            
        except Exception as e:
            print(f"Ошибка создания интерактивной DOS: {e}")
            return None