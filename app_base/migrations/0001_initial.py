# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AppCfg',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('app_type', models.CharField(max_length=40, verbose_name='\u5e94\u7528\u7c7b\u578b\uff0c\u4f8b\u5982oracle,mysql,slee\u7b49')),
                ('app_name', models.CharField(max_length=40, verbose_name='\u5e94\u7528\u7684\u540d\u79f0,\u4f8b\u5982oracle\u4e2d\u7684\u5b9e\u4f8b\u540d')),
                ('app_alias', models.CharField(max_length=40, verbose_name='\u5e94\u7528\u7684\u522b\u540d\u79f0,\u4f8b\u5982oracle\u4e2d\u7684\u522b\u540d,\u4f8b\u5982oracle\u4e2d\u7684db_unique_name')),
                ('base_path', models.CharField(max_length=512, verbose_name='\u5e94\u7528\u7684base\u8def\u5f84\uff0c\u4f8b\u5982$ORACLE_HOME\uff0c\u901a\u8fc7base\u8def\u5f84\u53ef\u4ee5\u4f7f\u7528\u76f8\u5bf9\u8def\u5f84\u53bb\u8bbf\u95ee\u6587\u4ef6\u6216\u662f\u6267\u884c\u547d\u4ee4')),
                ('thread_filter_regex', models.CharField(max_length=100, verbose_name='\u76f8\u5173\u5e94\u7528\u8fdb\u7a0b\u8fc7\u6ee4\u6b63\u5219\u8868\u8fbe\u5f0f')),
                ('relative_port', models.CharField(max_length=40, verbose_name='\u5e94\u7528\u5173\u8054\u7aef\u53e3,\u591a\u4e2a\u7aef\u53e3\u7528;\u5206\u5272')),
                ('profile', models.CharField(max_length=1024, verbose_name='\u5e94\u7528\u7684\u73af\u5883\u53d8\u91cf\u6587\u4ef6,\u591a\u4e2a\u6587\u4ef6\u7528;\u5206\u5272')),
                ('cfg_file', models.CharField(max_length=1024, verbose_name='\u5e94\u7528\u914d\u7f6e\u6587\u4ef6,\u591a\u4e2a\u914d\u7f6e\u6587\u4ef6\u7528;\u5206\u5272')),
                ('log_file_dir', models.CharField(max_length=255, verbose_name='\u5e94\u7528\u65e5\u5fd7\u6587\u4ef6\u6240\u5728\u76ee\u5f55')),
                ('log_file_name', models.CharField(max_length=255, verbose_name='\u5f53\u524d\u6b63\u5728\u4f7f\u7528\u65e5\u5fd7\u6587\u4ef6\u540d,\u591a\u4e2a\u65e5\u5fd7\u6587\u4ef6\u7528;\u5206\u5272')),
                ('log_file_name_regex', models.CharField(max_length=512, verbose_name='\u5e94\u7528\u65e5\u5fd7\u6587\u4ef6\u540d\u6b63\u5219\u8868\u8fbe\u5f0f\uff0c\u7528\u6765\u5339\u914d\u6240\u6709\u7684\u5e94\u7528\u7684\u65e5\u5fd7\u6587\u4ef6')),
                ('include_dir', models.CharField(max_length=1024, verbose_name='\u4e0d\u5728base\u76ee\u5f55\u4e0b\u4e14\u540c\u5e94\u7528\u5173\u8054\u7684\u76ee\u5f55,\u591a\u4e2a\u76ee\u5f55\u7528;\u5206\u5272')),
                ('ignore_dir', models.CharField(max_length=1024, verbose_name='\u5728base\u76ee\u5f55\u4e0b\u4f46\u65e0\u9700\u5173\u6ce8\u7684\u76ee\u5f55,\u591a\u4e2a\u76ee\u5f55\u7528;\u5206\u5272')),
                ('ignore_ext', models.CharField(max_length=255, verbose_name='\u5e94\u7528base\u76ee\u5f55\u4e0b\u65e0\u9700\u5173\u6ce8\u7684\u6587\u4ef6\u7c7b\u578b,\u591a\u4e2aext\u7528;\u5206\u5272')),
                ('comment', models.CharField(max_length=512, verbose_name='\u5907\u6ce8')),
                ('create_time', models.DateTimeField(verbose_name='\u521b\u5efa\u65f6\u95f4')),
                ('update_time', models.DateTimeField(verbose_name='\u6700\u540e\u4e00\u6b21\u4fee\u6539\u65f6\u95f4')),
            ],
            options={
                'verbose_name': '\u5e94\u7528\u914d\u7f6e',
                'verbose_name_plural': '\u5e94\u7528\u914d\u7f6e',
            },
        ),
        migrations.CreateModel(
            name='AppPriStbyCfg',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tag', models.CharField(max_length=128, verbose_name='\u4e3b\u5907\u914d\u7f6e\u6807\u7b7e')),
                ('availble_ip', models.CharField(max_length=40, verbose_name='\u540c\u4e00\u7f51\u6bb5\u4e2d\u53ef\u4ee5\u7528\u6765\u5207\u6362\u7528\u7684\u672a\u88ab\u4f7f\u7528ip')),
            ],
            options={
                'verbose_name': '\u5e94\u7528\u4e3b\u5907\u914d\u7f6e',
                'verbose_name_plural': '\u5e94\u7528\u4e3b\u5907\u914d\u7f6e',
            },
        ),
        migrations.CreateModel(
            name='AppTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('app_type', models.CharField(max_length=40, verbose_name='\u5e94\u7528\u7c7b\u578b\uff0c\u4f8b\u5982oracle,mysql,slee\u7b49')),
                ('app_name', models.CharField(max_length=40, verbose_name='\u7f3a\u7701\u5e94\u7528\u7684\u540d\u79f0,\u4f8b\u5982oracle\u4e2d\u7684\u5b9e\u4f8b\u540d')),
                ('app_alias', models.CharField(max_length=40, verbose_name='\u7f3a\u7701\u5e94\u7528\u7684\u522b\u540d\u79f0,\u4f8b\u5982oracle\u4e2d\u7684\u522b\u540d,\u4f8b\u5982oracle\u4e2d\u7684db_unique_name')),
                ('base_path', models.CharField(max_length=512, verbose_name='\u7f3a\u7701\u5e94\u7528\u7684base\u8def\u5f84\uff0c\u4f8b\u5982$ORACLE_HOME\uff0c\u901a\u8fc7base\u8def\u5f84\u53ef\u4ee5\u4f7f\u7528\u76f8\u5bf9\u8def\u5f84\u53bb\u8bbf\u95ee\u6587\u4ef6\u6216\u662f\u6267\u884c\u547d\u4ee4')),
                ('thread_filter_regex', models.CharField(max_length=100, verbose_name='\u7f3a\u7701\u76f8\u5173\u5e94\u7528\u8fdb\u7a0b\u8fc7\u6ee4\u6b63\u5219\u8868\u8fbe\u5f0f')),
                ('relative_port', models.CharField(max_length=40, verbose_name='\u7f3a\u7701\u5e94\u7528\u5173\u8054\u7aef\u53e3,\u591a\u4e2a\u7aef\u53e3\u7528;\u5206\u5272')),
                ('profile', models.CharField(max_length=1024, verbose_name='\u7f3a\u7701\u5e94\u7528\u7684\u73af\u5883\u53d8\u91cf\u6587\u4ef6,\u591a\u4e2a\u6587\u4ef6\u7528;\u5206\u5272')),
                ('cfg_file', models.CharField(max_length=1024, verbose_name='\u7f3a\u7701\u5e94\u7528\u914d\u7f6e\u6587\u4ef6,\u591a\u4e2a\u914d\u7f6e\u6587\u4ef6\u7528;\u5206\u5272')),
                ('log_file_dir', models.CharField(max_length=255, verbose_name='\u7f3a\u7701\u5e94\u7528\u65e5\u5fd7\u6587\u4ef6\u6240\u5728\u76ee\u5f55')),
                ('log_file_name', models.CharField(max_length=255, verbose_name='\u7f3a\u7701\u5f53\u524d\u6b63\u5728\u4f7f\u7528\u65e5\u5fd7\u6587\u4ef6\u540d,\u591a\u4e2a\u65e5\u5fd7\u6587\u4ef6\u7528;\u5206\u5272')),
                ('log_file_name_regex', models.CharField(max_length=512, verbose_name='\u7f3a\u7701\u5e94\u7528\u65e5\u5fd7\u6587\u4ef6\u540d\u6b63\u5219\u8868\u8fbe\u5f0f\uff0c\u7528\u6765\u5339\u914d\u6240\u6709\u7684\u5e94\u7528\u7684\u65e5\u5fd7\u6587\u4ef6')),
                ('include_dir', models.CharField(max_length=1024, verbose_name='\u7f3a\u7701\u4e0d\u5728base\u76ee\u5f55\u4e0b\u4e14\u540c\u5e94\u7528\u5173\u8054\u7684\u76ee\u5f55,\u591a\u4e2a\u76ee\u5f55\u7528;\u5206\u5272')),
                ('ignore_dir', models.CharField(max_length=1024, verbose_name='\u7f3a\u7701\u5728base\u76ee\u5f55\u4e0b\u4f46\u65e0\u9700\u5173\u6ce8\u7684\u76ee\u5f55,\u591a\u4e2a\u76ee\u5f55\u7528;\u5206\u5272')),
                ('ignore_ext', models.CharField(max_length=255, verbose_name='\u7f3a\u7701\u5e94\u7528base\u76ee\u5f55\u4e0b\u65e0\u9700\u5173\u6ce8\u7684\u6587\u4ef6\u7c7b\u578b,\u591a\u4e2aext\u7528;\u5206\u5272')),
                ('comment', models.CharField(max_length=512, verbose_name='\u5907\u6ce8')),
                ('create_time', models.DateTimeField(verbose_name='\u521b\u5efa\u65f6\u95f4')),
                ('update_time', models.DateTimeField(verbose_name='\u6700\u540e\u4e00\u6b21\u4fee\u6539\u65f6\u95f4')),
            ],
            options={
                'verbose_name': '\u5e94\u7528\u5b9a\u4e49\u6a21\u677f',
                'verbose_name_plural': '\u5e94\u7528\u5b9a\u4e49\u6a21\u677f',
            },
        ),
        migrations.CreateModel(
            name='Server',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('host_ip', models.CharField(max_length=40, verbose_name='\u4e3b\u673aip')),
                ('host_name', models.CharField(max_length=40, verbose_name='\u4e3b\u673a\u540d')),
                ('server_type', models.IntegerField(verbose_name='\u670d\u52a1\u5668\u7c7b\u578b1\u3001linux\u670d\u52a1\u5668\uff0c2\u3001windows\u670d\u52a1\u5668')),
                ('access_type', models.IntegerField(verbose_name='\u8bbf\u95ee\u65b9\u5f0f\uff0c1\u3001ssh\u767b\u5f55\uff0c2\u3001\u901a\u8fc7\u84dd\u9cb8agent\u8bbf\u95ee')),
                ('status', models.IntegerField(verbose_name='\u670d\u52a1\u5668\u5f53\u524d\u72b6\u6001\uff0c1\u3001\u6b63\u5e38\u4f7f\u7528\uff0c2\u3001\u4e0d\u5728\u4f7f\u7528\uff0c3\u3001\u7ef4\u4fee\u4e2d')),
                ('ssh_port', models.IntegerField(verbose_name='ssh\u767b\u5f55\u7aef\u53e3')),
                ('comment', models.CharField(max_length=255, verbose_name='\u5907\u6ce8')),
                ('create_time', models.DateTimeField(verbose_name='\u521b\u5efa\u65f6\u95f4')),
                ('update_time', models.DateTimeField(verbose_name='\u6700\u540e\u4e00\u6b21\u4fee\u6539\u65f6\u95f4')),
            ],
            options={
                'verbose_name': '\u5e94\u7528\u670d\u52a1\u5668',
                'verbose_name_plural': '\u5e94\u7528\u670d\u52a1\u5668',
            },
        ),
        migrations.CreateModel(
            name='ServerUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('login_name', models.CharField(max_length=40, verbose_name='\u7528\u6237\u767b\u5f55\u540d')),
                ('pass_word', models.CharField(max_length=20, verbose_name='\u7528\u6237\u767b\u5f55\u5bc6\u7801')),
                ('create_time', models.DateTimeField(verbose_name='\u521b\u5efa\u65f6\u95f4')),
                ('update_time', models.DateTimeField(verbose_name='\u4fee\u6539\u65f6\u95f4')),
                ('server', models.ForeignKey(to='app_base.Server')),
            ],
            options={
                'verbose_name': '\u670d\u52a1\u5668\u7528\u6237',
                'verbose_name_plural': '\u670d\u52a1\u5668\u7528\u6237',
            },
        ),
        migrations.AddField(
            model_name='apppristbycfg',
            name='app_template',
            field=models.ForeignKey(to='app_base.AppTemplate'),
        ),
        migrations.AddField(
            model_name='apppristbycfg',
            name='pri_app',
            field=models.ForeignKey(related_name='primary_app', to='app_base.AppCfg'),
        ),
        migrations.AddField(
            model_name='apppristbycfg',
            name='stby_app',
            field=models.ForeignKey(related_name='standby_app', to='app_base.AppCfg'),
        ),
        migrations.AddField(
            model_name='appcfg',
            name='app_template',
            field=models.ForeignKey(to='app_base.AppTemplate'),
        ),
        migrations.AddField(
            model_name='appcfg',
            name='app_user',
            field=models.ForeignKey(related_name='app_user', to='app_base.ServerUser'),
        ),
        migrations.AddField(
            model_name='appcfg',
            name='root_user',
            field=models.ForeignKey(related_name='root_user', to='app_base.ServerUser'),
        ),
        migrations.AddField(
            model_name='appcfg',
            name='server',
            field=models.ForeignKey(to='app_base.Server'),
        ),
    ]
