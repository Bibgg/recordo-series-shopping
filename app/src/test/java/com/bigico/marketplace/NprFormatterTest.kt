package com.bigico.marketplace

import org.junit.Assert.assertEquals
import org.junit.Test

class NprFormatterTest {
    @Test
    fun formatsNepaleseRupeesWithGrouping() {
        assertEquals("रु 1,250", NprFormatter.format(1250))
    }

    @Test
    fun formatsZeroWithoutDecimalPlaces() {
        assertEquals("रु 0", NprFormatter.format(0))
    }
}
