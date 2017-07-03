##QMUI iOS设计原理分析
###引入
QMUI是腾讯开源的一套UI框架，目前支持Web和iOS平台，Android平台正在努力更新中。

本文针对iOS平台1.3.6版本的实现进行分析。QMUI iOS的当前版本为1.7.2，其设计目的是用于辅助快速搭建一个具备基本设计还原效果的iOS项目，同时利用自身提供的丰富控件及兼容处理，让开发者能专注于业务需求而无需耗费精力在基础代码的设计上。不管是新项目的创建，或是已有项目的维护，均可使开发效率和项目质量得到大幅度提升。
###示例
进入项目的示例demo，找到程序的入口AppDelegate，其主功能模块为：

```
- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
    
    // 启动QMUI的配置模板  先加载一个默认的模版，在QMUIConfigurationTemplate里面可以对需要调整的参数做调整
    [QMUIConfigurationTemplate setupConfigurationTemplate];
    
    // 将全局的控件样式渲染出来
    [QMUIConfigurationManager renderGlobalAppearances]; // -->如何发挥作用 通过UIAppearance!!
    
    // QD自定义的全局样式渲染
    [QDCommonUI renderGlobalAppearances];//自定义的部分
    
    // 将状态栏设置为希望的样式 -->四种状态
    [QMUIHelper renderStatusBarStyleLight];
    
    // 预加载 QQ 表情资源，避免第一次使用时卡顿，耗时操作，所以用异步
    dispatch_async(dispatch_get_global_queue(0, 0), ^{
        [QMUIQQEmotionManager emotionsForQQ];
    });
    
    // 界面
    self.window = [[UIWindow alloc] initWithFrame:[[UIScreen mainScreen] bounds]];
    [self createTabBarController];
    
    // 启动动画
    [self startLaunchingAnimation];
    
    return YES;
}
```

这里面主要包括了QMUIConfigurationTemplate、QMUIConfigurationManager、QDCommonUI、QMUIHelper、QMUIQQEmotionManager几个类，在程序启动之前需要先对它们进行初始化。
###QMUIConfigurationTemplate
进入
[QMUIConfigurationTemplate setupConfigurationTemplate]函数的实现，我们发现整个实现是在对QMUICMI这个宏进行一些函数调用和参赛修改。查看一下QMUICMI的定义

```
#define QMUICMI [QMUIConfigurationManager sharedInstance]
```

发现它是QMUIConfigurationManager的一个单例。

再回到[QMUIConfigurationTemplate setupConfigurationTemplate]函数的实现，我们发现函数中先调用了QMUIConfigurationManager单例中的initDefaultConfiguration方法，该方法的大致实现如下：

```
- (void)initDefaultConfiguration {
    
    #pragma mark - Global Color
    ...
    #pragma mark - UIWindowLevel
    ...
    #pragma mark - UIControl
    ...
    #pragma mark - UIButton
    ...
    ...
}
```

在QMUIConfigurationManager中同时有这么些属性：

```
#pragma mark - Global Color

@property(nonatomic, strong) UIColor         *clearColor;
@property(nonatomic, strong) UIColor         *whiteColor;
@property(nonatomic, strong) UIColor         *blackColor;
@property(nonatomic, strong) UIColor         *grayColor;
@property(nonatomic, strong) UIColor         *grayDarkenColor;
@property(nonatomic, strong) UIColor         *grayLightenColor;
@property(nonatomic, strong) UIColor         *redColor;
@property(nonatomic, strong) UIColor         *greenColor;
@property(nonatomic, strong) UIColor         *blueColor;
@property(nonatomic, strong) UIColor         *yellowColor;
...
#pragma mark - UIWindowLevel

@property(nonatomic, assign) CGFloat         windowLevelQMUIAlertView;
@property(nonatomic, assign) CGFloat         windowLevelQMUIActionSheet;
@property(nonatomic, assign) CGFloat         windowLevelQMUIMoreOperationController;
@property(nonatomic, assign) CGFloat         windowLevelQMUIImagePreviewView;
...
#pragma mark - UIControl

@property(nonatomic, assign) CGFloat         controlHighlightedAlpha;
@property(nonatomic, assign) CGFloat         controlDisabledAlpha;

@property(nonatomic, strong) UIColor         *segmentTextTintColor;
@property(nonatomic, strong) UIColor         *segmentTextSelectedTintColor;
@property(nonatomic, strong) UIFont          *segmentFontSize;
...
...
```

由此可知QMUIConfigurationManager单例中的initDefaultConfiguration方法是用来对QMUIConfigurationManager的属性进行初始化工作，完成这步后，在[QMUIConfigurationTemplate setupConfigurationTemplate]函数的接下来部分可以对一些参赛选择性的修改。

总结一下，QMUIConfigurationTemplate是一个对QMUIConfigurationManager进行初始化和修改的类，QMUIConfigurationManager中保存着许多属性，可能在程序中会被调用。

###QMUIConfigurationManager
由前面部分，我们可以对QMUIConfigurationManager的功能有个初步的认识，进入QMUIConfiguration.h文件，我们可以找到与QMUIConfigurationManager属性相关的宏定义。

```
#define QMUICMI [QMUIConfigurationManager sharedInstance]


#pragma mark - Global Color

// 基础颜色
#define UIColorClear                [QMUICMI clearColor]
...

// 功能颜色
#define UIColorLink                 [QMUICMI linkColor]                       // 全局统一文字链接颜色
#define UIColorDisabled             [QMUICMI disabledColor]                   // 全局统一文字disabled颜色
...

// 测试用的颜色
#define UIColorTestRed              [QMUICMI testColorRed]
...

// 可操作的控件
#pragma mark - UIControl

#define UIControlHighlightedAlpha       [QMUICMI controlHighlightedAlpha]          // 一般control的Highlighted透明值
#define UIControlDisabledAlpha          [QMUICMI controlDisabledAlpha]             // 一般control的Disable透明值
...
...

```

在QMUIConfiguration.h中，QMUIConfigurationManager的所有属性都被宏定义了一遍。

在AppDelegate中还调用了[QMUIConfigurationManager renderGlobalAppearances]，其实现如下：

```
+ (void)renderGlobalAppearances {
    
    // QMUIButton
    [QMUINavigationButton renderNavigationButtonAppearanceStyle];  //对`UINavigationBar`上的`UIBarButton`做统一的样式调整
    [QMUIToolbarButton renderToolbarButtonAppearanceStyle]; ///// 对UIToolbar上的UIBarButtonItem做统一的样式调整
    
    // UINavigationBar
    UINavigationBar *navigationBarAppearance = [UINavigationBar appearance];
    [navigationBarAppearance setBarTintColor:NavBarBarTintColor];
    [navigationBarAppearance setBackgroundImage:NavBarBackgroundImage forBarMetrics:UIBarMetricsDefault];
    [navigationBarAppearance setShadowImage:NavBarShadowImage];
    
    // UIToolBar
    UIToolbar *toolBarAppearance = [UIToolbar appearance];
    [toolBarAppearance setBarTintColor:ToolBarBarTintColor];
    [toolBarAppearance setBackgroundImage:ToolBarBackgroundImage forToolbarPosition:UIBarPositionAny barMetrics:UIBarMetricsDefault];
    [toolBarAppearance setShadowImage:[UIImage qmui_imageWithColor:ToolBarShadowImageColor size:CGSizeMake(1, PixelOne) cornerRadius:0] forToolbarPosition:UIBarPositionAny];
    
    // UITabBar
    UITabBar *tabBarAppearance = [UITabBar appearance];
    [tabBarAppearance setBarTintColor:TabBarBarTintColor];
    [tabBarAppearance setBackgroundImage:TabBarBackgroundImage];
    [tabBarAppearance setShadowImage:[UIImage qmui_imageWithColor:TabBarShadowImageColor size:CGSizeMake(1, PixelOne) cornerRadius:0]];
    
    
    // UITabBarItem
    UITabBarItem *tabBarItemAppearance = [UITabBarItem appearanceWhenContainedIn:[QMUITabBarViewController class], nil];
    [tabBarItemAppearance setTitleTextAttributes:@{NSForegroundColorAttributeName:TabBarItemTitleColor} forState:UIControlStateNormal];
    [tabBarItemAppearance setTitleTextAttributes:@{NSForegroundColorAttributeName:TabBarItemTitleColorSelected} forState:UIControlStateSelected];
}

```

这里面主要功能函数有+ (instancetype)appearance 和+ (instancetype)appearanceWhenContainedIn:函数，它们是属于UIAppearance协议中的函数，每个遵循了UIAppearance的UI组件都可以调用这两个方法，来对app中被调用时进行统一初始化。由此可知[QMUIConfigurationManager renderGlobalAppearances]函数的调用是用来对app中的组件进行全局的初始化。

总结一下，QMUIConfigurationManager这个类，即有保存属性状态的功能，又有初始化app中UI组建的功能。与QMUIConfigurationTemplate相结合，可以知道用QMUIConfigurationTemplate可以进行更多的个性化定制，而QMUIConfigurationManager做更多的统一化处理，于是工程中也把QMUIConfigurationManager放置于框架类作为功能模块使用，而QMUIConfigurationTemplate则作为模版放置在工程中。

###其他
QDCommonUI是一个对子类化的UI组件进行全局统一配置的类，在示例中留出了一些接口，关于在QMUI中如何进行子类化将在下次分享中进行讨论。

QMUIHelper是一个工具类，在它的UIApplication分类中有四个函数接口可以设置不同的状态栏风格：

```
/**
 * 更改状态栏内容颜色为深色
 *
 * @warning 需在Info.plist文件内设置字段“View controller-based status bar appearance”的值为“NO”才能生效
 */
+ (void)renderStatusBarStyleDark;

/**
 * 更改状态栏内容颜色为浅色
 *
 * @warning 需在Info.plist文件内设置字段“View controller-based status bar appearance”的值为“NO”才能生效
 */
+ (void)renderStatusBarStyleLight;

/**
 * 把App的主要window置灰，用于浮层弹出时，请注意要在适当时机调用`resetDimmedApplicationWindow`恢复到正常状态
 */
+ (void)dimmedApplicationWindow;

/**
 * 恢复对App的主要window的置灰操作，与`dimmedApplicationWindow`成对调用
 */
+ (void)resetDimmedApplicationWindow;
```
QMUIQQEmotionManager是一个为输入框添加QQ表情的工具类，需要配合其他几个类共同使用。在AppDelegate，我们用异步的方式调用[QMUIQQEmotionManager emotionsForQQ]函数，此函数的作用是将文件目录下的图片添加到一个数组中去，操作比较耗时，所以安排在程序一启动就进行加载，并采用异步方式不阻塞主线程。


在程序启动中完成以上这些工作，就可以安心的加载我们的程序主界面和启动动画了。
