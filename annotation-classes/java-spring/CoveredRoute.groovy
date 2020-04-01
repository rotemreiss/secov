package com.mypackage.test.security

@interface CoveredRoute {
    String path() default "";
    String method() default "";
}