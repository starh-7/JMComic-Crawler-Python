from jmcomic import *
from jmcomic.cl import JmcomicUI

# 下方填入你要下载的本子的id，一行一个，每行的首尾可以有空白字符
jm_albums = '''

502931
503914
506262
649590
1013148
520151
651332
611634
531774
602619
647460
121307
569566
647737
649156
561552
551662
641338
634804
612863
623265
418516
602611
602409
604166
600115
590284
588994
589549
581563
582718
578865
578238
575369
513102
577181
575828
574794
572494
567744
567625
568782
566735
558114
564049
564029
367504
384995
140424
33842
520134
560169
404743
401862
369533
446983
402126
401671
558374
554488
523385
527494
431469
413735
388694
554770
443571
404597
376148
245292
353156
528214
408924
411608
391292
369634
408425
514367
441598
346863
368062
368647
367559
310057
473327
380840
368321
531549
369529
496106
235800
371568
373399
520907
367584
367583
492550
531303
404601
516847
118464
299064
547588
519901
545453
544354
543453
541165
536942
540871
540655
539892
536764
535961
536015
531987
500945
532921
531464
498105
527443
380773
526216
521352
515820
517506
517165
516851
515830
516074
510411
502016
485676
511726
511913
512132
509472
510544
509857
507784
508784
507000
506628
344548
506579
502963
502116
502432
501839
500089
499294
495963
498910
486745
474364
473701
261812
330248
471884
395792
89177
281134
425048
414754
144431
318001
468641
207010
326810
85574
398745
340357
465321
465025
397797
322071
120602
270387
384323
258850
252087
446706
463493
249641
374299
456157
235221
13364
287216
391951
6641
231548
226652
463720
431841
374058
454867
462722
463262
112852
103628
136733
457670
431397
452738
374815
404786
457395
374277
400688
370096
370196
459564
16776
459241
378049
145051
366867
377686
457291
454411
354551
428982
457219
453589
90699
372726
355306
452600
426219
447233
404477
450858
250296
392126
216874
303307
103532
374026
450836
441217
395009
446485
296830
410593
413555
449590
374030
448519
95249
371819
448129
419622
445863
446285
400210
203812
281456
446051
446054
446055
358686
333901
300253
401904
122916
427149
333217
442616
442921
337391
413014
294262
439640
441627
439649
438251
423768
188631
620565
379756
439191
275504
147896
125566
315935
329888
438060
285813
397645
430151
308749
433275
271316
433676
264322
405642
17650
11170
428964
386249
404476
404474
364243
431200
431197
430793
428590
408827
428442
428430
428589
428628
428227
427415
139406
110562
427756
428221
77350
147082
377795
147358
280913
104973
84687
426532
399054
427111
394450
291029
237005
229719
380049
424491
315562
349771
378587
406369
321576
79171
147348
381800
267567
21689
37037
424068
218611
183595
412641
379821
399532
416140
423585
98988
422938
399896
334721
416365
421455
320788
421074
371877
143519
224141
319877
401614
408254
206025
357478
121674
418979
87785
347448
419040
372787
80561
394430
419980
356960
419286
419400
419026
417137
413547
413144
411792
405868
404129
267052
266660
404942
404585
404952
404784
404417
392639
301440
397022
198205
208518
375337
387612
386204
385763
380326
379988
219656
372250
363675
198128
151036
349883


'''

# 单独下载章节
jm_photos = '''



'''


def env(name, default, trim=('[]', '""', "''")):
    import os
    value = os.getenv(name, None)
    if value is None or value == '':
        return default

    for pair in trim:
        if value.startswith(pair[0]) and value.endswith(pair[1]):
            value = value[1:-1]

    return value


def get_id_set(env_name, given):
    aid_set = set()
    for text in [
        given,
        (env(env_name, '')).replace('-', '\n'),
    ]:
        aid_set.update(str_to_set(text))

    return aid_set


def main():
    album_id_set = get_id_set('JM_ALBUM_IDS', jm_albums)
    photo_id_set = get_id_set('JM_PHOTO_IDS', jm_photos)

    helper = JmcomicUI()
    helper.album_id_list = list(album_id_set)
    helper.photo_id_list = list(photo_id_set)

    option = get_option()
    helper.run(option)
    option.call_all_plugin('after_download')


def get_option():
    # 读取 option 配置文件
    option = create_option(os.path.abspath(os.path.join(__file__, '../../assets/option/option_workflow_download.yml')))

    # 支持工作流覆盖配置文件的配置
    cover_option_config(option)

    # 把请求错误的html下载到文件，方便GitHub Actions下载查看日志
    log_before_raise()

    return option


def cover_option_config(option: JmOption):
    dir_rule = env('DIR_RULE', None)
    if dir_rule is not None:
        the_old = option.dir_rule
        the_new = DirRule(dir_rule, base_dir=the_old.base_dir)
        option.dir_rule = the_new

    impl = env('CLIENT_IMPL', None)
    if impl is not None:
        option.client.impl = impl

    suffix = env('IMAGE_SUFFIX', None)
    if suffix is not None:
        option.download.image.suffix = fix_suffix(suffix)


def log_before_raise():
    jm_download_dir = env('JM_DOWNLOAD_DIR', workspace())
    mkdir_if_not_exists(jm_download_dir)

    def decide_filepath(e):
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)

        if resp is None:
            suffix = str(time_stamp())
        else:
            suffix = resp.url

        name = '-'.join(
            fix_windir_name(it)
            for it in [
                e.description,
                current_thread().name,
                suffix
            ]
        )

        path = f'{jm_download_dir}/【出错了】{name}.log'
        return path

    def exception_listener(e: JmcomicException):
        """
        异常监听器，实现了在 GitHub Actions 下，把请求错误的信息下载到文件，方便调试和通知使用者
        """
        # 决定要写入的文件路径
        path = decide_filepath(e)

        # 准备内容
        content = [
            str(type(e)),
            e.msg,
        ]
        for k, v in e.context.items():
            content.append(f'{k}: {v}')

        # resp.text
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)
        if resp:
            content.append(f'响应文本: {resp.text}')

        # 写文件
        write_text(path, '\n'.join(content))

    JmModuleConfig.register_exception_listener(JmcomicException, exception_listener)


if __name__ == '__main__':
    main()
