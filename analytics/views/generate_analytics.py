import StringIO
import os
import random

import pandas as pd

import xlsxwriter
from django.http import HttpResponse
from google.cloud import storage

from rest_framework import generics

from formats.formats import Formats as format

from academics.models import Class
from setup.models import School


class GenerateAnalytics(generics.ListCreateAPIView):
    def get(self, request, *args, **kwargs):
        school_id = request.query_params.get('school_id')
        school = School.objects.get(id=school_id)
        standard = request.query_params.get('standard')
        the_class = Class.objects.get(school=school, standard=standard)

        storage_client = storage.Client()
        bucket = storage_client.get_bucket('classup')

        master_data_file = '%s_%s_master_data.xlsx' % (str(school_id), the_class)
        file_path = 'classup2/Analytics/school/%s/%s' % (str(school_id), master_data_file)
        blob = bucket.blob(file_path)
        local_path = 'analytics/%s' % master_data_file
        blob.download_to_filename(local_path)

        analytics_file_name = 'class_%s_analytics.xlsx' % the_class
        output = StringIO.StringIO(analytics_file_name)
        analytics = xlsxwriter.Workbook(output)

        fmt = format()
        title_format = analytics.add_format(fmt.get_title())
        title_format.set_border()
        header = analytics.add_format(fmt.get_header())
        big_font = analytics.add_format(fmt.get_large_font())
        big_font.set_color('#33691E')
        medium_font = analytics.add_format(fmt.get_medium_fong())
        medium_font.set_color('#827717')
        section_heading = analytics.add_format(fmt.get_section_heading())
        section_heading.set_color('#4E342E')
        cell_bold = analytics.add_format(fmt.get_cell_bold())
        cell_bold.set_border()
        cell_normal = analytics.add_format(fmt.get_cell_normal())
        cell_normal.set_border()
        cell_left = analytics.add_format(fmt.get_cell_left())
        cell_left.set_border()
        cell_small = analytics.add_format(fmt.get_cell_small())
        cell_small.set_border()
        cell_red = analytics.add_format(fmt.get_cell_red())
        cell_green = analytics.add_format(fmt.get_cell_green())
        perc_format = analytics.add_format(fmt.get_perc_format())
        big_perc_format = analytics.add_format(fmt.get_big_perc_format())
        perc_format.set_color('#37474F')
        colors = fmt.get_colors()

        sheets = ['Term I']
        for a_sheet in sheets:
            sheet = pd.read_excel(local_path, sheet_name=a_sheet, index_col=0)
            wb_sheet = analytics.add_worksheet(a_sheet)
            wb_sheet.set_landscape()
            wb_sheet.set_paper(9)  # A4 paper
            wb_sheet.fit_to_pages(1, 0)
            header_text = 'Analytics Sheet Class %s' % (the_class)
            wb_sheet.set_header('&L%s&RPage &P of &N' % header_text)
            wb_sheet.merge_range('A1:L1', '%s Analytics for class %s term: %s' % (school, the_class, a_sheet),
                                 title_format)
            student_df = sheet['Student']
            total_students = student_df.count()
            wb_sheet.set_column('B:B', 4)
            wb_sheet.set_column('C:C', 14)
            wb_sheet.set_column('D:D', 10)
            wb_sheet.set_column('E:E', 12)
            wb_sheet.set_column('F:F', 12)
            wb_sheet.set_column('G:G', 10)
            wb_sheet.set_column('H:H', 14)
            wb_sheet.set_column('I:I', 10)
            wb_sheet.set_column('J:J', 14)
            wb_sheet.set_column('K:K', 7)
            row = 2
            col = 3
            wb_sheet.merge_range(row, col, row + 1, col,  'Class', medium_font)
            col += 1
            wb_sheet.merge_range(row, col, row + 1, col, the_class.standard, big_font)
            col += 1
            wb_sheet.merge_range(row, col, row + 1, col, 'Students', medium_font)
            col += 1
            wb_sheet.merge_range(row, col, row + 1, col, total_students, big_font)
            col += 1

            sections_df = sheet['Section']
            sections = sections_df.unique()
            wb_sheet.merge_range(row, col, row + 1, col, 'Sections', medium_font)
            col += 1
            wb_sheet.merge_range(row, col, row + 1, col, sections_df.nunique(), big_font)

            # student section wise distribution analytics
            section_wise_students = sections_df.value_counts()
            student_in_section = []
            for section in sections:
                student_in_section.append(section_wise_students[section])

            row += 4
            col = 4
            categories = [a_sheet, row, col, row + sections_df.nunique() - 1, col]
            wb_sheet.write_column(row, col, sections, cell_bold)
            col += 1
            values = [a_sheet, row, col, row + sections_df.nunique() - 1, col]
            wb_sheet.write_column(row, col, student_in_section, cell_bold)
            chart = analytics.add_chart({'type': 'column'})
            chart.set_style(28)
            chart.set_legend({'none': True})
            chart.set_y_axis({
                'visible': False,
                'major_gridlines': {'visible': False},
                'min': 0,
                'max': 50
            })
            chart.add_series({
                'categories': categories,
                'values': values,
                'marker': {'type': 'automatic'},
                'gradient': {'colors': ['#311B92', '#7986CB']},
                'data_labels': {'value': True},
            })
            chart.set_title({
                'name': 'Section wise Students',
                'name_font': {
                    'size': 14,
                    'color': colors[random.randrange(len(colors))]
                }
            })
            wb_sheet.insert_chart('D6', chart, {'x_offset': 10, 'y_offset': 0})

            # total marks analytics for all sections
            row = 20
            col = 3
            wb_sheet.merge_range(row, col, row + 1, col + 2, 'Total Marks Analysis', section_heading)
            total_marks_df = sheet[['Student', 'Section', 'Total']]
            max_marks = 700.00
            row += 2
            wb_sheet.merge_range(row, col, row + 1, col, 'Highest', medium_font)
            col += 1
            highest = round(total_marks_df['Total'].max(), 2) / max_marks
            wb_sheet.merge_range(row, col, row + 1, col, highest, big_perc_format)
            col += 1
            wb_sheet.merge_range(row, col, row + 1, col, 'Average', medium_font)
            col += 1
            average = round(total_marks_df['Total'].mean(), 2) / max_marks
            wb_sheet.merge_range(row, col, row + 1, col, average, big_perc_format)
            col += 1
            wb_sheet.merge_range(row, col, row + 1, col, 'Min', medium_font)
            col += 1
            min = round(total_marks_df['Total'].min(), 2) / max_marks
            wb_sheet.merge_range(row, col, row + 1, col, min, big_perc_format)

            # analytics for each section separate - highest, average and min
            row += 4
            col = 4
            wb_sheet.write_string(row, col, 'Section', cell_bold)
            col += 1
            wb_sheet.write_string(row, col, 'Highest', cell_bold)
            col += 1
            wb_sheet.write_string(row, col, 'Average', cell_bold)
            col += 1
            wb_sheet.write_string(row, col, 'Min', cell_bold)
            row += 1
            col = 4
            wb_sheet.write_column(row, col, sections, cell_bold)

            # as we have consolidated analytics for all sections readily available, insert it now
            row += sections_df.nunique()
            wb_sheet.write_string(row, col, 'All Sections', cell_bold)
            col += 1
            wb_sheet.write_number(row, col, highest, perc_format)
            col += 1
            wb_sheet.write_number(row, col, average, perc_format)
            col += 1
            wb_sheet.write_number(row, col, min, perc_format)

            # now, go to the top of this table to insert section specific analytics
            row -= sections_df.nunique()
            col = 5
            categories = [a_sheet, row, col - 1, row + sections_df.nunique(), col - 1]

            for section in sections:
                subset = total_marks_df['Section'] == section
                highest = round(total_marks_df[subset]['Total'].max() / max_marks, 2)
                wb_sheet.write_number(row, col, highest, perc_format)
                col += 1
                average = round(total_marks_df[subset]['Total'].mean() / max_marks, 2)
                wb_sheet.write_number(row, col, average, perc_format)
                col += 1
                min = round(total_marks_df[subset]['Total'].min() / max_marks, 2)
                wb_sheet.write_number(row, col, min, perc_format)
                row += 1
                col = 5
            chart = analytics.add_chart({'type': 'column'})
            chart.set_style(26)
            chart.set_legend({'position': 'bottom'})
            chart.set_y_axis({
                'major_gridlines': {'visible': False},
                'min': 0,
                'max': 1
            })
            values = [a_sheet, row - sections_df.nunique(), col, row, col]
            chart.add_series({
                'categories': categories,
                'name': 'Highest',
                'values': values,
                'marker': {'type': 'automatic'},
                'data_labels': {
                    'value': True,
                    'font': {
                        'name': 'Consolas',
                        'size': 8,
                    }
                },
                'gradient': {'colors': ['#1B5E20', '#66BB6A']},
                'overlap': 0,
            })
            col += 1
            values = [a_sheet, row - sections_df.nunique(), col, row, col]
            chart.add_series({
                'name': 'Average',
                'values': values,
                'marker': {'type': 'automatic'},
                'gradient': {'colors': ['#9E9D24', '#D4E157']},
                'data_labels': {
                    'value': True,
                    'font': {
                        'name': 'Consolas',
                        'size': 8,
                        'rotation': -90
                    }
                },
            })
            col += 1
            values = [a_sheet, row - sections_df.nunique(), col, row, col]
            chart.add_series({
                'name': 'Min',
                'values': values,
                'marker': {'type': 'automatic'},
                'gradient': {'colors': ['#FF5252', '#B71C1C']},
                'data_labels': {
                    'value': True,
                    'font': {
                        'name': 'Consolas',
                        'size': 8,
                        'rotation': -90
                    }
                },
            })
            chart.set_title({
                'name': 'Class %s - Section wise Total marks comparison' % the_class,
                'name_font': {
                    'name': 'Calibri',
                    'color': colors[random.randrange(len(colors))],
                    'size': 12
                }
            })
            row = 36
            col = 0
            wb_sheet.insert_chart(row, col, chart, {'x_offset': 20, 'y_offset': 10})

            # show the names of top 10 students
            top_10 = total_marks_df.nlargest(10, ['Total'])
            row += 1
            col = 7
            wb_sheet.merge_range(row, col, row, col + 4, 'Class %s Top 10 students' % the_class, header)
            row += 1
            wb_sheet.write_string(row, col, 'Rank', cell_bold)
            col += 1
            wb_sheet.merge_range(row, col, row, col + 1, 'Student', cell_bold)
            col += 2
            wb_sheet.write_string(row, col, 'Section', cell_bold)
            col += 1
            wb_sheet.write_string(row, col, '%', cell_bold)

            row += 1
            col = 7
            s_no = 1
            for idx in top_10.index:
                wb_sheet.write_number(row, col, s_no, cell_normal)
                s_no += 1
                col += 1
                wb_sheet.merge_range(row, col, row, col + 1, top_10['Student'][idx], cell_normal)
                col += 2
                wb_sheet.write_string(row, col, top_10['Section'][idx], cell_normal)
                col += 1
                wb_sheet.write_number(row, col, top_10['Total'][idx] / max_marks, perc_format)
                row += 1
                col = 7

            # student distribution in percentage segments (> 85, 85-70, 70-50, < 50)
            slabs = ['Above 85%', 'Between 85%-70%', 'Between 70%-50%', 'Below 50%']
            slab_values = []
            above_85 = total_marks_df[total_marks_df['Total'] >= (max_marks * .85)]['Student'].count()
            print('above_85=%d' % above_85)
            slab_values.append(round(float(above_85) / float(total_students), 2))
            between_85_70 = total_marks_df[(total_marks_df['Total'] < (max_marks * .85)) & (total_marks_df['Total'] >
                                                                                            (max_marks * .70))][
                'Student'].count()
            print('between_85_70=%d' % between_85_70)
            slab_values.append(round(float(between_85_70) / float(total_students), 2))
            between_70_50 = total_marks_df[(total_marks_df['Total'] < (max_marks * .7)) & (total_marks_df['Total'] >
                                                                                           (max_marks * .50))][
                'Student'].count()
            print('between_70_50=%d' % between_70_50)
            slab_values.append(round(float(between_70_50) / float(total_students), 2))
            below_50 = total_marks_df[total_marks_df['Total'] <= (max_marks * .5)]['Student'].count()
            print('below_50=%d' % below_50)
            slab_values.append(round(float(below_50) / float(total_students), 2))
            print(slab_values)

            row += 5
            col = 5
            wb_sheet.merge_range(row, col, row + 1, col + 2, 'Total Marks Slab wise', medium_font)
            col += 1
            row += 2
            wb_sheet.write_column(row, col, slabs)
            categories = [a_sheet, row, col, row + 3, col]
            col += 1
            wb_sheet.write_column(row, col, slab_values, perc_format)
            values = [a_sheet, row, col, row + 3, col]
            col = 5

            chart = analytics.add_chart({'type': 'pie'})
            chart.set_style(10)
            chart.set_legend({'position': 'bottom'})
            chart.set_title({
                'name': 'Class %s - Slab Wise Marks All Section ' % the_class,
                'name_font': {
                    'name': 'Calibri',
                    'color': colors[random.randrange(len(colors))],
                    'size': 12
                }
            })
            col += 1
            chart.add_series({
                'categories': categories,
                'values': values,
                'data_labels': {
                    'value': True,
                    'position': 'outside_end',
                    'leader_lines': True
                },
                'points': [
                    {'gradient': {'colors': ['#1B5E20', '#A5D6A7']}},
                    {'gradient': {'colors': ['#01579B', '#039BE5']}},
                    {'gradient': {'colors': ['#9E9D24', '#D4E157']}},
                    {'gradient': {'colors': ['#FF5252', '#B71C1C']}},
                ],
            })
            col = 3
            wb_sheet.insert_chart(row, col, chart, {'x_offset': 25, 'y_offset': 0})

            # Show slab wise distribution of marks for each section separately
            row += 17
            col = 0
            wb_sheet.merge_range(row, col, row + 1, col + 5, 'Slab Wise Total Marks for Each Section', medium_font)
            idx1 = 0
            for section in sections:
                print('total marks slab wise for section: %s' % section)
                this_section_df = total_marks_df[total_marks_df['Section'] == section]
                student_count = student_in_section[idx1]
                idx1 += 1
                slab_values = []
                above_85 = this_section_df[this_section_df['Total'] >= (max_marks * .85)]['Student'].count()
                print('above_85=%d' % above_85)
                slab_values.append(round(float(above_85) / float(student_count), 2))
                between_85_70 = \
                    this_section_df[(this_section_df['Total'] < (max_marks * .85)) & (this_section_df['Total'] >
                                                                                      (max_marks * .70))][
                        'Student'].count()
                print('between_85_70=%d' % between_85_70)
                slab_values.append(round(float(between_85_70) / float(student_count), 2))
                between_70_50 = \
                    this_section_df[(this_section_df['Total'] < (max_marks * .7)) & (this_section_df['Total'] >
                                                                                     (max_marks * .50))][
                        'Student'].count()
                print('between_70_50=%d' % between_70_50)
                slab_values.append(round(float(between_70_50) / float(student_count), 2))
                below_50 = this_section_df[this_section_df['Total'] <= (max_marks * .5)]['Student'].count()
                print('below_50=%d' % below_50)
                slab_values.append(round(float(below_50) / float(student_count), 2))
                print(slab_values)

                row += 2
                col = 3
                wb_sheet.write_column(row, col, slabs)
                categories = [a_sheet, row, col, row + 3, col]
                col += 1
                wb_sheet.write_column(row, col, slab_values, perc_format)
                values = [a_sheet, row, col, row + 3, col]

                chart = analytics.add_chart({'type': 'pie'})
                chart.set_style(10)
                chart.set_size({'x_scale': .8, 'y_scale': .85})
                chart.set_legend({'position': 'right'})
                chart.set_title({
                    'name': 'Class %s-%s - Slab Wise Marks ' % (the_class, section),
                    'name_font': {
                        'name': 'Calibri',
                        'color': colors[random.randrange(len(colors))],
                        'size': 12
                    }
                })
                chart.add_series({
                    'categories': categories,
                    'values': values,
                    'data_labels': {
                        'value': True,
                        'position': 'outside_end',
                        'leader_lines': True
                    },
                    'points': [
                        {'gradient': {'colors': ['#1B5E20', '#A5D6A7']}},
                        {'gradient': {'colors': ['#01579B', '#039BE5']}},
                        {'gradient': {'colors': ['#9E9D24', '#D4E157']}},
                        {'gradient': {'colors': ['#FF5252', '#B71C1C']}},
                    ],
                })
                col = 1
                wb_sheet.insert_chart(row, col, chart, {'x_offset': 0, 'y_offset': 0})

                # besides this pie chart show the toppers (> 85%) & trailers (< 50%) students
                toppers = this_section_df[this_section_df['Total'] > (max_marks * .85)].nlargest(20, 'Total')
                trailers = this_section_df[this_section_df['Total'] < (max_marks * .5)].nsmallest(20, 'Total')
                col = 7
                wb_sheet.merge_range(row, col, row, col + 1, 'Students in Top Slab', header)
                wb_sheet.merge_range(row, col + 2, row, col + 3, 'Students in Bottom Slab', header)
                row += 1
                topper_row = row
                trailers_row = row
                for idx in toppers.index:
                    wb_sheet.write_string(topper_row, col, toppers['Student'][idx], cell_green)
                    col += 1
                    wb_sheet.write_number(topper_row, col, toppers['Total'][idx] / max_marks, perc_format)
                    topper_row += 1
                    col = 7
                col = 9
                for idx in trailers.index:
                    wb_sheet.write_string(trailers_row, col, trailers['Student'][idx], cell_red)
                    col += 1
                    wb_sheet.write_number(trailers_row, col, trailers['Total'][idx] / max_marks, perc_format)
                    trailers_row += 1
                    col = 9
                row += 15
                col = 0

            subject_list = [
                'English', 'Hindi', 'Mathematics', 'Science', 'Social Studies', 'Computer'
            ]
            row += 1
            for subject in subject_list:
                wb_sheet.merge_range(row, col, row + 1, col + 4, 'Subject Analysis: %s' % subject, section_heading)
                subject_df = sheet[['Student', 'Section', subject]]
                max_marks = 100.00
                highest = round(subject_df[subject].max(), 2) / max_marks
                print('highest in %s: %.2f' % (subject, highest))
                average = round(subject_df[subject].mean(), 2) / max_marks
                print('average in %s: %.2f' % (subject, average))
                min = round(subject_df[subject].min(), 2) / max_marks
                print('min in %s: %.2f' % (subject, min))

                row += 3
                col += 4
                wb_sheet.write_string(row, col, 'Section', cell_small)
                col += 1
                wb_sheet.write_string(row, col, 'Highest', cell_small)
                col += 1
                wb_sheet.write_string(row, col, 'Average', cell_small)
                col += 1
                wb_sheet.write_string(row, col, 'Min', cell_small)
                row += 1
                col -= 3
                wb_sheet.write_column(row, col, sections, cell_small)
                row += sections_df.nunique()
                wb_sheet.write_string(row, col, 'All Sections', cell_small)
                # as we have consolidated analytics for all sections readily available, insert it now
                col += 1
                wb_sheet.write_number(row, col, highest, perc_format)
                col += 1
                wb_sheet.write_number(row, col, average, perc_format)
                col += 1
                wb_sheet.write_number(row, col, min, perc_format)

                # now, go to the top of this table to insert section specific analytics
                row -= sections_df.nunique()
                col -= 2
                categories = [a_sheet, row, col - 1, row + sections_df.nunique(), col - 1]

                for section in sections:
                    subset = subject_df['Section'] == section
                    highest = round(subject_df[subset][subject].max() / max_marks, 2)
                    print('highest in %s section %s: %.2f' % (subject, section, highest))
                    wb_sheet.write_number(row, col, highest, perc_format)
                    col += 1

                    average = round(subject_df[subset][subject].mean() / max_marks, 2)
                    print('average in %s section %s: %.2f' % (subject, section, average))
                    wb_sheet.write_number(row, col, average, perc_format)
                    col += 1

                    min = round(subject_df[subset][subject].min() / max_marks, 2)
                    print('min in %s section %s: %.2f' % (subject, section, min))
                    wb_sheet.write_number(row, col, min, perc_format)
                    col = 5
                    row += 1
                chart = analytics.add_chart({'type': 'column'})
                chart.set_style(28)
                chart.set_legend({'position': 'bottom'})
                chart.set_y_axis({
                    'major_gridlines': {'visible': False},
                    'min': 0,
                    'max': 1
                })
                values = [a_sheet, row - sections_df.nunique(), col, row, col]
                chart.add_series({
                    'categories': categories,
                    'name': 'Highest',
                    'values': values,
                    'marker': {'type': 'automatic'},
                    'data_labels': {
                        'value': True,
                        'font': {
                            'name': 'Consolas',
                            'size': 8,
                        }
                    },
                    'gradient': {'colors': ['#1B5E20', '#66BB6A']},
                    'overlap': 0,
                })
                col += 1
                values = [a_sheet, row - sections_df.nunique(), col, row, col]
                chart.add_series({
                    'name': 'Average',
                    'values': values,
                    'marker': {'type': 'automatic'},
                    'gradient': {'colors': ['#9E9D24', '#D4E157']},
                    'data_labels': {
                        'value': True,
                        'font': {
                            'name': 'Consolas',
                            'size': 8,
                            'rotation': -90
                        }
                    },
                })
                col += 1
                values = [a_sheet, row - sections_df.nunique(), col, row, col]
                chart.add_series({
                    'name': 'Min',
                    'values': values,
                    'marker': {'type': 'automatic'},
                    'gradient': {'colors': ['#FF5252', '#B71C1C']},
                    'data_labels': {
                        'value': True,
                        'font': {
                            'name': 'Consolas',
                            'size': 8,
                            'rotation': -90
                        }
                    },
                })
                chart.set_title({
                    'name': 'Class %s - Section wise %s marks comparison' % (the_class, subject),
                    'name_font': {
                        'name': 'Calibri',
                        'color': colors[random.randrange(len(colors))],
                        'size': 12
                    }
                })
                row -= sections_df.nunique() + 2
                col = 3
                wb_sheet.insert_chart(row, col, chart, {'x_offset': 20, 'y_offset': 20})

                # show the names of top & bottom 10 students in this subject
                row += 20
                col = 1
                wb_sheet.merge_range(row, col, row, col + 3,
                                     'Class %s Top 10 students in %s' % (the_class, subject), header)
                wb_sheet.merge_range(row, col + 5, row, col + 8,
                                     'Class %s Bottom 10 students in %s' % (the_class, subject), header)
                row += 1
                wb_sheet.write_string(row, col, 'Rank', cell_bold)
                wb_sheet.write_string(row, col + 5, 'Rank', cell_bold)
                col += 1
                wb_sheet.write_string(row, col, 'Student', cell_bold)
                wb_sheet.write_string(row, col + 5, 'Student', cell_bold)
                col += 1
                wb_sheet.write_string(row, col, 'Section', cell_bold)
                wb_sheet.write_string(row, col + 5, 'Section', cell_bold)
                col += 1
                wb_sheet.write_string(row, col, '%', cell_bold)
                wb_sheet.write_string(row, col + 5, '%', cell_bold)
                row += 1
                col -= 3
                rank = 1
                top_10 = subject_df.nlargest(10, subject)
                for idx in top_10.index:
                    wb_sheet.write_number(row, col, rank, cell_small)
                    rank += 1
                    col += 1
                    wb_sheet.write_string(row, col, top_10['Student'][idx], cell_green)
                    col += 1
                    wb_sheet.write_string(row, col, top_10['Section'][idx], cell_small)
                    col += 1
                    wb_sheet.write_number(row, col, top_10[subject][idx] / max_marks, perc_format)
                    row += 1
                    col -= 3

                rank = 1
                bottom_10 = subject_df.nsmallest(10, subject)
                row -= 10
                col += 5
                for idx in bottom_10.index:
                    wb_sheet.write_number(row, col, rank, cell_small)
                    rank += 1
                    col += 1
                    wb_sheet.write_string(row, col, bottom_10['Student'][idx], cell_red)
                    col += 1
                    wb_sheet.write_string(row, col, bottom_10['Section'][idx], cell_small)
                    col += 1
                    wb_sheet.write_number(row, col, bottom_10[subject][idx] / max_marks, perc_format)
                    row += 1
                    col -= 3

                # student distribution in percentage segments (> 85, 85-70, 70-50, < 50)
                col = 0
                row += 2
                wb_sheet.merge_range(row, col, row + 1, col + 5, '%s - Marks slab wise' % subject, medium_font)
                idx1 = 0
                for section in sections:
                    if section == 'A':
                        row += 3
                        col = 1
                    if section == 'B':
                        col = 7
                    if section == 'C':
                        row += 15
                        col = 1
                    if section == 'D':
                        col = 7

                    slab_values = []
                    this_section_df = subject_df[subject_df['Section'] == section]
                    student_count = student_in_section[idx1]
                    idx1 += 1
                    above_85 = this_section_df[this_section_df[subject] >= (max_marks * .85)][subject].count()
                    print('above_85=%d' % above_85)
                    slab_values.append(round(float(above_85) / float(student_count), 2))
                    between_85_70 = \
                        this_section_df[(this_section_df[subject] < (max_marks * .85)) & (this_section_df[subject] >
                                                                                          (max_marks * .70))][
                            subject].count()
                    print('between_85_70=%d' % between_85_70)
                    slab_values.append(round(float(between_85_70) / float(student_count), 2))
                    between_70_50 = \
                        this_section_df[(this_section_df[subject] < (max_marks * .7)) & (this_section_df[subject] >
                                                                                         (max_marks * .50))][
                            subject].count()
                    print('between_70_50=%d' % between_70_50)
                    slab_values.append(round(float(between_70_50) / float(student_count), 2))
                    below_50 = this_section_df[this_section_df[subject] <= (max_marks * .5)][subject].count()
                    print('below_50=%d' % below_50)
                    slab_values.append(round(float(below_50) / float(student_count), 2))

                    wb_sheet.write_column(row, col, slabs)
                    categories = [a_sheet, row, col, row + 3, col]
                    col += 1
                    wb_sheet.write_column(row, col, slab_values, perc_format)
                    values = [a_sheet, row, col, row + 3, col]

                    chart = analytics.add_chart({'type': 'doughnut'})
                    chart.set_style(14)
                    chart.set_size({'x_scale': .8, 'y_scale': .85})
                    chart.set_legend({'position': 'right'})
                    chart.set_title({
                        'name': 'Class %s-%s %s - Slab Wise Marks ' % (the_class, section, subject),
                        'name_font': {
                            'name': 'Calibri',
                            'color': colors[random.randrange(len(colors))],
                            'size': 12
                        }
                    })
                    chart.add_series({
                        'categories': categories,
                        'values': values,
                        'data_labels': {
                            'value': True,
                            'font': {
                                'name': 'Calibri',
                                'color': '#3E2723',
                                'size': 8
                            }
                        },
                        'points': [
                            {'gradient': {'colors': ['#1B5E20', '#A5D6A7']}},
                            {'gradient': {'colors': ['#01579B', '#039BE5']}},
                            {'gradient': {'colors': ['#9E9D24', '#D4E157']}},
                            {'gradient': {'colors': ['#FF5252', '#B71C1C']}},
                        ],
                    })
                    if section in ['A', 'C']:
                        col = 1
                    else:
                        col = 6
                    wb_sheet.insert_chart(row, col, chart, {'x_offset': 0, 'y_offset': 0})
                wb_sheet.set_h_pagebreaks([row + 15])
                row += 19
                col = 0

        os.remove(local_path)
        try:
            analytics.close()
        except Exception as e:
            print(e.message, type(e))
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=%s' % analytics_file_name
        response.write(output.getvalue())
        return response
