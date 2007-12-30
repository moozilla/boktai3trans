<?xml version="1.0" encoding="ISO-8859-1"?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:key name="elemKey" match="element" use="@name"/>
<xsl:template match="elements" />

<xsl:key name="typePrefixKey" match="type-prefixes/type" use="@name"/>
<xsl:template match="type-prefixes" />

<xsl:key name="typePostfixKey" match="type-postfixes/type" use="@name"/>
<xsl:template match="type-postfixes" />

<xsl:key name="typeURLKey" match="type-urls/type" use="@name"/>
<xsl:template match="type-urls" />

<xsl:key name="dungeonURLKey" match="dungeon-urls/dungeon-url" use="@name"/>
<xsl:template match="dungeon-urls" />

<xsl:template match="monsters">

<html>
<head>
<title>Boktai 3 Guide - Monsters</title>
<style type="text/css">

body { background-color: #f5f5dc; font-family: Arial; }

.monster { border: 1px outset; background-color: white; float: left; margin: 3px; padding: 2px; min-width: 242px; min-height: 262px; }
.monster .icon { border: 1px inset; padding: 1px; margin: 1px; float: left; }
.monster .data { float: left; }
.monster .name { border: 1px inset; font-weight: bold; padding: 0px 2px 0px 2px; margin: 1px; float: left; }
.monster .elem { border: 1px inset;  margin: 1px; padding: 0px 1px 0px 1px; float: left; }
.monster .stat { clear: left; float: left; font-size: 16px; }
.monster .drop { border: 1px inset; margin: 1px; padding: 0px 2px 2px 2px; clear: left; float: left; min-width: 80px; }
.monster .locd { clear: left; float: left; padding-left: 8px; margin: 1px; font-weight: bold; font-size: 12px; }
.monster .locs { border: 1px inset; margin: 1px 1px 1px 10px; padding: 0px 2px 2px 2px; font-weight: normal; font-size: 14px; width: 200px; }
.monster .dscd { clear: left; float: left; padding-left: 8px; margin: 1px; font-weight: bold; font-size: 12px; }
.monster .dscs { border: 1px inset; margin: 1px 1px 1px 10px; padding: 0px 2px 1px 2px; font-weight: normal; font-size: 14px; width: 200px; }
.monster .atkd { clear: left; float: left; padding-left: 8px; margin: 1px; font-weight: bold; font-size: 12px; }
.monster .atks { border: 1px inset; margin: 1px 1px 1px 10px; padding: 0px 2px 1px 2px; font-weight: normal; font-size: 14px; width: 200px; }
.monster img { vertical-align: text-bottom; }

</style>
</head>
<body>
<h2>Monsters</h2>

<xsl:apply-templates />

<div style="clear: left;" />

</body>
</html>

</xsl:template>

<xsl:template match="monster">
  <div class="monster">
    <div class="icon"><img src="images/m{@number}.gif" /></div>
    <div class="data">
      <div class="name">
        <a name="{@number}"><xsl:value-of select="@number"/></a>
        <xsl:text> </xsl:text>
        <xsl:value-of select="@name"/>
      </div>
      <xsl:apply-templates select="@element" />
      <xsl:apply-templates select="@sunweak" />
      <div class="drop">
        <xsl:choose>
          <xsl:when test="common-drop">
            <xsl:apply-templates select="common-drop" />
          </xsl:when>
          <xsl:otherwise>
            <div><img src="images/noitem.png" /> n/a</div>
          </xsl:otherwise>
        </xsl:choose>
        <xsl:choose>
          <xsl:when test="rare-drop">
            <xsl:apply-templates select="rare-drop" />
          </xsl:when>
          <xsl:otherwise>
            <div><img src="images/noitem.png" /> n/a</div>
          </xsl:otherwise>
        </xsl:choose>
      </div>
    </div>
    <xsl:apply-templates select="locations" />
    <xsl:apply-templates select="description" />
    <xsl:apply-templates select="attacks" />
  </div>
</xsl:template>

<xsl:template match="@element">
  <div class="elem">
    <img src="images/{key('elemKey',.)}" />
  </div>
</xsl:template>

<xsl:template match="@sunweak">
  <xsl:if test=". = 'true'">
    <div class="elem">
      <img src="images/sunweak.gif" />
    </div>
  </xsl:if>
</xsl:template>

<xsl:template match="common-drop|rare-drop">
  <div>
    <img src="images/{key('typePrefixKey',type)}{number}{key('typePostfixKey',type)}.png" />
    <xsl:text> </xsl:text>
    <a href="{key('typeURLKey',type)}#{number}"><xsl:value-of select="name"/></a>
  </div>
</xsl:template>

<xsl:template match="locations">
  <div class="locd">
    Location(s):
    <div class="locs">
      <xsl:choose>
        <xsl:when test="dungeon">
          <xsl:apply-templates select="dungeon" />
        </xsl:when>
        <xsl:otherwise>
          ???
        </xsl:otherwise>
      </xsl:choose>
    </div>
  </div>
</xsl:template>

<xsl:template match="dungeon">
  <div>
    <xsl:element name="a">
      <xsl:attribute name="target">_MAP</xsl:attribute>
      <xsl:attribute name="href">
        <xsl:value-of select="key('dungeonURLKey',@name)" />
        <xsl:text>?mark=</xsl:text>

        <xsl:for-each select="location">
          <xsl:if test="position() > 1">
            <xsl:text>|</xsl:text>
          </xsl:if>
          <xsl:value-of select="@area" />
          <xsl:text>,</xsl:text>
          <xsl:value-of select="@x" />
          <xsl:text>,</xsl:text>
          <xsl:value-of select="@y" />
          <xsl:text>,r</xsl:text>
        </xsl:for-each>

      </xsl:attribute>
      <xsl:value-of select="@name" />
    </xsl:element>
    <xsl:text> (L</xsl:text>
    <xsl:value-of select="@level" />
    <xsl:text> </xsl:text>
    <xsl:value-of select="@life" />
    <xsl:text>HP </xsl:text>
    <xsl:value-of select="@exp" />
    <xsl:text>XP)</xsl:text>
  </div>
</xsl:template>

<xsl:template match="description">
  <div class="dscd">
    Description:
    <div class="dscs">
      <xsl:value-of select="text()"/>
    </div>
  </div>
</xsl:template>

<xsl:template match="attacks">
  <div class="atkd">
    Attacks:
    <div class="atks">
      <xsl:apply-templates select="attack" />
    </div>
  </div>
</xsl:template>

<xsl:template match="attack">
  <div>
    <xsl:value-of select="@name"/>
    <xsl:text>: </xsl:text>
    <xsl:value-of select="@damage"/>
    <xsl:if test="@element">
      <xsl:text> </xsl:text>
      <img src="images/{key('elemKey',@element)}" />
    </xsl:if>
  </div>
</xsl:template>

</xsl:stylesheet>
