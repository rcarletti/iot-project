CONTIKI_PROJECT = coapbit

#PROJECT_SOURCEFILES += data.c

all: $(CONTIKI_PROJECT)

CONTIKI=/home/rossella/contiki

# linker optimizations
SMALL=1

APPS += er-coap
APPS += rest-engine

# for some platforms
UIP_CONF_IPV6=1
# IPv6 make config disappeared completely
CFLAGS += -DUIP_CONF_IPV6=1

CFLAGS += -DPROJECT_CONF_H=\"project-conf.h\"

CFLAGS += -DUIP_CONF_TCP=0

include $(CONTIKI)/Makefile.include
