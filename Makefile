# Makefile for ICCP Nodemap AD LDAP Sync
#
# Vars
PYTHON = python3
BASEDIR = /taiga/admin/iccp/nodemap
VENV_DIR = $(BASEDIR)/venv_set-proxy
VENV_PYTHON = $(VENV_DIR)/bin/$(PYTHON)
BIN_DIR = $(BASEDIR)/bin
BIN_FILES = add_group.py add_ncsa_ad_group.py add_user.py nodemap nodemap_info hostvenv
CRON_DIR = $(BASEDIR)/cron
CRON_FILES = gen_ad_passwd.py get_lustre_idmap.sh nodemap_cron.sh push_lustre_idmap.sh push_pwgr_extras.sh sync_groups_ad.py sync_group_idmap.py sync_groups_ncsa_ad.py user_nodemap.py
MGS_DIR = /root/nodemap
MGS_FILES = get_idmap_gids get_idmap_uids nodemap_add_cron.sh nodemap_add_groups.sh nodemap_add_users.sh nodemap_del_groups.sh

# Targets
.PHONY: all venv bin cron mgs

$(BASEDIR):
	mkdir -p $(BASEDIR)

$(CRON_DIR):
	mkdir -p $(CRON_DIR)

venv: $(VENV_DIR)

$(VENV_DIR):
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements.txt

bin: $(BIN_DIR)
	cp $(BIN_FILES) $(BIN_DIR)/

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

cron: $(CRON_DIR)
	cp $(CRON_FILES) $(CRON_DIR)/

$(MGS_DIR):
	mkdir -p $(MGS_DIR)

mgs: $(MGS_DIR)
	cp $(MGS_FILES) $(MGS_DIR)/

